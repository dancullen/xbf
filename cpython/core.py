import glob
import hashlib
import logging
import logging.handlers
import os
import struct
import subprocess
import sys
import time
from typing import Optional, List, Tuple

from digi.xbee.devices import XBeeDevice
from digi.xbee.filesystem import FileSystemException, LocalXBeeFileSystemManager
from digi.xbee.models.address import XBee64BitAddress
from digi.xbee.models.message import XBeeMessage
from digi.xbee.models.protocol import XBeeProtocol
from digi.xbee.util.utils import disable_logger
import mpy_cross
import serial

API_MODE_WITHOUT_ESCAPES = 0x01
MAIN_PY = "/flash/main.py"

Error = str
Success = None


# new_error returns a new error, annotated with context.
# Inspired by https://godoc.org/errors#New
def new_error(message: str) -> Error:
    calling_func = sys._getframe().f_back.f_code.co_name
    return Error("%s: %s" % (calling_func, message))


# errorf is used to wrap an existing error with details before it gets returned up the call stack.
# Inspired by https://golang.org/pkg/fmt/#Errorf
def errorf(format_str: str, *args) -> Error:
    calling_func = sys._getframe().f_back.f_code.co_name
    return Error("%s: %s" % (calling_func, format_str % args))


# func provides context for a given line number, which helps to improve error logging. It is similar to __func__ in C.
# https://stackoverflow.com/questions/8759359/equivalent-of-func-from-c-in-python
def func():
    calling_func = sys._getframe().f_back.f_code.co_name
    return calling_func


# log abstracts the logging so that we have the flexibility to change the sink.
def log(msg: str) -> None:
    logger = logging.getLogger()
    if len(logger.handlers) == 0:  # Looks like user hasn't configured the root logger, so just use print instead.
        print(msg)
    else:
        logger.info(msg)


# logc invokes log() after prefixing the message with some context. (logc = log with context)
def logc(msg: str) -> None:
    calling_func = sys._getframe().f_back.f_code.co_name
    log("%s: %s" % (calling_func, msg))


# setup_logging sets up the root logger to log to stderr and optionally also to a rotating log file.
def setup_logging(enable_file_logging: bool = False,
                  log_dir_name: str = "logs",
                  log_file_name: str = "log.txt",
                  max_file_size: int = 5 * 1024 * 1024,
                  max_num_files: int = 5,
                  show_context=False) -> Error:

    log_format = "%(asctime)s: %(message)s"
    if show_context:
        log_format = "%(asctime)s:%(levelname)s:%(filename)s:%(lineno)s: %(message)s"

    log_level = logging.INFO

    # Set up the root logger to log to stderr.
    logging.basicConfig(level=log_level, format=log_format)

    # Disable logging in the xbee-python library. https://xbplib.readthedocs.io/en/latest/user_doc/logging_events.html
    loggers = ["digi.xbee.devices", "digi.xbee.reader", "digi.xbee.firmware", "digi.xbee.serial"]
    for name in loggers:
        disable_logger(name)

    if not enable_file_logging:
        return Success

    # Set up the root logger to also log to file.
    logger = logging.getLogger()
    destination = os.path.join(log_dir_name, log_file_name)
    try:
        if not os.path.isdir(log_dir_name):
            os.makedirs(log_dir_name)
    except Exception as ex:
        return Error("%s: Unable to create log directory %s. Reason: %s." % (func(), log_dir_name, ex))

    handler = logging.handlers.RotatingFileHandler(filename=destination,
                                                   maxBytes=max_file_size,
                                                   backupCount=max_num_files)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)

    return Success


class OpenXBeeDevice:
    """
    OpenXBeeDevice is a context manager for digi.xbee.devices.XBeeDevice (and its subclasses).
    This class ensures that the serial port gets properly closed even if an error occurs.
    """

    def __init__(self, xbee):
        self.xbee = xbee
        self.log = print

    def __enter__(self):
        self.log("Opening XBee 3 device...")
        self.xbee.open()
        self.log("Opened XBee 3 device.")
        return self.xbee

    def __exit__(self, exc_type, exc_value, traceback):
        if self.xbee is not None and self.xbee.is_open():
            self.xbee.close()
        self.log("Closed XBee 3 device.")


class BindReceiveCallback:
    """
    BindReceiveCallback is a context manager for setting up receive callbacks on digi.xbee.devices.XBeeDevice.

    Note: To receive messages with xbee-python, you definitely want to use the callback approach.
    Polling seems to run MUCH slower for some unknown reason (like an order of magnitude slower).
    """

    def __init__(self, xbee: XBeeDevice, receiver):
        """
        __init__ takes the XBeeDevice and the receiver, which is a class that contains the receive callback.
        It stores references to each, but the binding doesn't actually happen until __enter__.
        """
        self.xbee = xbee
        self.receiver = receiver

    def __enter__(self):
        self.xbee.add_data_received_callback(self._receive_callback)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.xbee.del_data_received_callback(self._receive_callback)

    def _receive_callback(self, msg: XBeeMessage) -> None:

        rx: bytearray = msg.data

        sender = msg.remote_device
        addr64: XBee64BitAddress = sender.get_64bit_addr()
        addr8bytes: bytearray = addr64.address

        self.receiver.receive(rx, addr8bytes)


class OpenFileSystem:
    """
    OpenFileSystem is a context manager for digi.xbee.filesystem.LocalXBeeFileSystemManager.
    This class ensures that the serial port gets properly closed even an error occurs.
    """
    def __init__(self, xbee):
        self.fs = LocalXBeeFileSystemManager(xbee)

    def __enter__(self):
        log("Opening XBee 3 filesystem...")
        self.fs.connect()
        log("Opened XBee 3 filesystem.")
        return self.fs

    def __exit__(self, exc_type, exc_value, traceback):
        self.fs.disconnect()
        log("Closed XBee 3 filesystem.")


def compile_py_to_mpy(py_file_path: str, mpy_file_path: str) -> Error:
    """ Cross-compiles the given .py file into a .mpy file. Assumes destination directory already exists. """

    # Remarks:
    # - Use "stdout=subprocess.PIPE" to capture the standard output.
    #   - https://docs.python.org/3/library/subprocess.html#subprocess.PIPE
    # - Use "stderr=subprocess.STDOUT" to redirect stderr to stdout.
    #   - https://stackoverflow.com/questions/11495783/redirect-subprocess-stderr-to-stdout
    # - Best practice dictates to call proc.kill() and invoke proc.communicate() again after a timeout occurs.
    #   - https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
    # - Popen.communicate() waits (blocks) until the process terminates or the timeout occurs.

    timeout_sec = 5.0
    timed_out = False

    args = ["-mno-unicode", "-msmall-int-bits=31", py_file_path, "-o", mpy_file_path]

    log("mpy_cross %s" % " ".join(args))

    proc: subprocess.Popen = mpy_cross.run(*args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        stdout_data, _ = proc.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout_data, _ = proc.communicate()
        timed_out = True

    log(stdout_data.decode("utf-8"))

    if timed_out:
        return Error("%s: mpy_cross failed! It took too long! timeout_sec=%s" % (func(), timeout_sec))

    if proc.returncode != 0:
        return Error("%s: mpy_cross failed! Exit status: %s" % (func(), proc.returncode))

    return Success


def build_mpy(src_dirs: List[str], build_dir: str) -> Error:
    """ Cross-compiles all .py files in SRC_DIR to .mpy files into BUILD_DIR. """

    # Ensure that destination directory exists.
    try:
        if not os.path.isdir(build_dir):
            os.makedirs(build_dir)
    except Exception as ex:
        return Error("%s: Unable to create directory %s. Details: %s." % (func(), build_dir, ex))

    for src_dir in src_dirs:

        py_files = glob.glob("%s/*.py" % src_dir)

        for py_file_path in py_files:

            py_file_name = os.path.basename(py_file_path)
            mpy_file_name = ".mpy".join(py_file_name.rsplit(".py"))  # Replace file extension.
            mpy_file_path = os.path.join(build_dir, mpy_file_name)

            err = compile_py_to_mpy(py_file_path, mpy_file_path)
            if err:
                return err


def shutdown_cleanly(xbee: XBeeDevice) -> Error:
    """
    Helper function to attempt to cleanly shut down the XBee.

    Note that only XBee 3 Cellular devices require a clean shutdown; this function
    behaves as a NOP for XBee 3 Zigbee/802.15.4/DigiMesh devices.

    You should invoke this function prior to issuing the ATFR command or removing power to the XBee.
    Otherwise, you risk corrupting/bricking the XBee's cell modem chip.
    For more info, see the "Clean shutdown" page in the XBee3 Cellular User Guide:
    https://www.digi.com/resources/documentation/Digidocs/90002258/#Reference/r_clean_shutdown.htm

    This function assumes that the XBee is currently in API Mode Without Escapes.

    The clean shutdown is performed by issuing the XBee 3 Cellular ATSD (Shutdown) command to the XBee module.
    Note that on XBee 3 Zigbee and 802.15.4 devices, the ATSD command does something completely different
    (SD = Scan Duration).

    Note that ATSD command does NOT put the XBee 3 Cellular device to sleep. Rather, it simply
    puts the XBee module (particularly its cell modem chip) into a state in which it is safe to power off.
    The XBee will continue to respond to API Frames messages even after it is in this shutdown state.

    Note that the XBee 3 Cellular ATSD command takes a long time to respond, usually somewhere between
    6 and 12 seconds, but it could be longer, so give it a nice long timeout, say 30 seconds, since
    that is what the user guide recommends for alternate airplane mode shutdown approach.

    We don't retry the shutdown command in a loop because a failure is highly unlikely.
    If the shutdown command fails, we report the error, but we don't do anything else--
    chances are you're still going to turn off the power no matter what, but at least
    we tried to shut down so gracefully.

    If the XBee 3 Cellular ATSD fails, we do attempt an alternate, fallback shutdown approach.

    Note that the shutdown command (ATSD) was not introduced until the August 2019 release of
    the XBee3 Cellular firmware, so older versions of firmware will need to rely upon this
    alternate approach.

    One approach mentioned on the [Clean shutdown page of the User Guide](
    https://www.digi.com/resources/documentation/Digidocs/90002258/#Reference/r_clean_shutdown.htm)
    is to de-assert the DTR_n/SLEEP_REQUEST pin and wait until the SLEEP_STATUS pin goes low.

    However, if your XBee carrier board hardware was not designed with this in mind, you won't
    be able to monitor this. Instead, we just wait for a specific reasonable amount of time, say 30 seconds.
    After all, this is a fallback shutdown approach, and this is better than nothing.
    However, there is another, bigger issue with the DTR_n/SLEEP_REQUEST approach:
    this pin might not be configured as a sleep request input! In other words, the XBee register "D8"
    might instead have it configured as a general-purposes digital I/O pin, in which case strobing
    this pin won't work. Since I don't want to make any assumptions about how the XBee is configured,
    I'm going to avoid the pin-based approach.

    So instead, we will use the third shutdown approach described in the User Guide:
    send the ATAM (Airplane Mode) command to put the device into airplane mode. Then we wait
    30 seconds as prescribed in the User Guide to give it plenty of time to shut down.

    Note that the ATAM (Airplane Mode) command gets applied immediately;
    no need to subsequently send ATAC (Apply Configuration) to apply the changes.
    """

    proto = xbee.get_protocol()
    if proto not in (XBeeProtocol.CELLULAR, XBeeProtocol.CELLULAR_NBIOT):
        log("%s: Device is not an XBee 3 Cellular; no need for clean shutdown. Bypassing clean shutdown." % func())
        return Success

    xbee_atsd_timeout_sec = 30
    xbee_time_to_wait_in_airplane_mode_sec = 30

    log("%s: Adjusting the xbee-python command timeout value..." % func())
    try:
        default_timeout_sec = xbee.get_sync_ops_timeout()  # Store default value so that we can put it back.
        xbee.set_sync_ops_timeout(xbee_atsd_timeout_sec)  # ATSD takes longer than most commands so give it extra time.
    except Exception as ex:
        return Error("%s: Failed to adjust the xbee-python command timeout value. Reason: " % (func(), ex))

    log("%s: Attempting to cleanly shut down the XBee. Sending shutdown command (ATSD)..." % func())
    try:
        xbee.execute_command("SD")
        log("%s: XBee shutdown command (ATSD) succeeded. Now safe to remove power from the module." % func())
        return Success
    except Exception as ex:
        log("%s: XBee shutdown command (ATSD) failed. Reason: %s. Will attempt fallback approach." % (func(), ex))
    finally:
        xbee.set_sync_ops_timeout(default_timeout_sec)

    log("%s: Attempting fallback approach to cleanly shut down. Sending ATAM command and waiting for %s seconds." %
        (func(), xbee_time_to_wait_in_airplane_mode_sec))
    try:
        xbee.set_parameter("AM", b"\x01")
    except Exception as ex:
        return Error("%s: XBee ATAM command failed. Reason: %s" % (func(), ex))

    time.sleep(xbee_time_to_wait_in_airplane_mode_sec)
    log("%s: Done waiting for XBee to enter airplane mode. You may now remove power from the module." % func())
    return Success


def restart_micropython_interpreter(xbee: XBeeDevice) -> Error:
    """
    Restarts the MicroPython interpreter.

    This allows  the latest version of main.py/main.mpy to run,
    assuming of course that Python Startup (ATPS) is enabled.

    Assumes the XBee is already in API Mode Without Escapes.

    Originally we hoped to implement this using the ATPYD command. As of 2019-09-23,
    the XBee3 Cellular User Guide recommends the command ATPYD to soft-reboot
    the MicroPython subsystem. However, this command no longer works, and it appears the docs
    are out of date. The comments at the bottom of JIRA XBPY-227 state, "we eliminated
    ATPYC and ATPYD in favor of ATPYB and ATPYE for clarity", so it seems that ATPYE is now
    the best command to use.

    HOWEVER, we discovered experimentally (and confirmed through discussions with the XBee team)
    that ATPYE command doesn't actually seem to re-run the main.mpy file.

    So we submitted a JIRA to request a new AT Command to perform a soft-reboot
    of the MicroPython subsystem: https://jira.digi.com/browse/XBPY-431

    For now, our workaround is to issue the ATFR (Firmware/Force Reset) command,
    after of course performing a clean shutdown (see the shutdown_cleanly() function)
    to prevent the possibility of cell modem module corruption. Note that non-cellular
    XBees do not need this clean shutdown, so shutdown_cleanly() amounts to a NOP.
    The ATFR is inelegant but there's not much else that we can do.

    References:
    - This page from the XBee3 Cellular User Guide: https://www.digi.com/resources/documentation/Digidocs/90002258/#Reference/r_cmd_PY.htm
    - This page from Digi MicroPython Programming Guide: https://www.digi.com/resources/documentation/digidocs/90002219/#tasks/t_erase_code.htm
    - More information about soft reset can be found on the following pages in the Digi MicroPython Programming Guide:
      - https://www.digi.com/resources/documentation/digidocs/90002219/#tasks/t_reset_repl.htm
      - https://www.digi.com/resources/documentation/digidocs/90002219/#tasks/t_run_code_startup.htm
    """

    log("%s: First perform a clean shutdown before we issue the firmware/force reset (FR) command..." % func())
    err = shutdown_cleanly(xbee)
    if err:
        log("%s: Unable to cleanly shut down the XBee. Details: %s. Proceeding with the FR command anyway." %
            (func(), err))

    log("%s: Now issuing the FR command..." % func())
    try:
        xbee.execute_command("FR")
    except Exception as ex:
        return Error("%s: XBee FR command failed. Reason: %s" % (func(), ex))

    log("%s: XBee FR command succeeded." % func())
    return Success


class XBeeFile:
    """" XBeeFile represents a file to be synchronized between the local PC and the XBee device. """

    def __init__(self, localpath):

        self.localpath = localpath

        log("Reading local file %s" % self.localpath)

        self.name = os.path.basename(self.localpath)

        with open(self.localpath, "rb") as fp:
            self.localdata = fp.read()

        h = hashlib.sha256()
        h.update(self.localdata)
        self.localhash = h.hexdigest()

        self.xbeepath = "/flash/%s" % self.name
        self.xbeehash = None

    def retrieve_xbeehash(self, fs):
        """ Updates self.xbeehash using the given OpenFileSystem object. """
        try:
            self.xbeehash = fs.get_file_hash(self.xbeepath)
        except FileSystemException as ex:
            self.xbeehash = None  # e.g., file does not exist.

    def __repr__(self):
        return "XBeeFile(localpath=%s, name=%s, len(localdata)=%s, localhash=%s, xbeepath=%s, xbeehash=%s)" % (
            self.localpath, self.name, len(self.localdata), self.localhash, self.xbeepath, self.xbeehash)


def api_frame_checksum(data: bytes) -> bytes:
    """
    Calculates the 8-bit checksum of the given data, returned as a byte array object of length 1.
    """
    checksum: int = 0
    for c in data:
        checksum += c           # Add all bytes
    checksum &= 0xFF            # Keep only the lowest 8 bits.
    checksum = 0xFF - checksum  # Subtract quantity from 0xFF.
    return bytes([checksum])    # https://stackoverflow.com/questions/21017698/converting-int-to-bytes-in-python-3


def api_frame_at_command(command: bytes, params: bytes) -> bytes:
    """
    Prepares the raw bytes for an API Frame containing an AT command (API Frame Type 0x08).
    """

    frame_type = b'\x08'
    frame_id = b'\x01'  # Don't leave frame ID as the value zero or else you won't get a response! Let's just use 0x01.

    frame = frame_type + frame_id + command + params

    start_char = b'\x7E'
    frame_len = struct.pack('>H', len(frame))  # Big-Endian uint16.

    packed = start_char + frame_len + frame + api_frame_checksum(frame)

    return packed


def enter_raw_AT_command_mode(ser: serial.Serial) -> Error:
    """
    enter_raw_AT_command_mode attempts to enter raw AT command mode by sending +++ followed by 1 sec of silence
    and then checking the response. Returns None on success or an error string if an error occurs.
    Assumes that `ser` has been set up with a suitable read timeout.
    """

    # Flush any previous data in the buffers before attempting to enter raw AT command mode.
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    tx = b'+++'
    logc("TX: %s" % tx)
    ser.write(tx)

    # 1 second of radio silence is required after the sending the +++ in order to enter raw AT command mode.
    time.sleep(1.0)

    rx = ser.read(3)
    logc("RX: %s" % rx)
    if rx != b'OK\r':
        return new_error("Did not get the 'OK' response.")

    return Success


def exit_raw_AT_command_mode(ser: serial.Serial) -> Error:
    """
    exit_raw_AT_command_mode invokes the ATCN command to exit out of raw AT Command mode.
    Assumes that you are currently in raw AT command mode to begin with.
    """
    tx = b'ATCN\r'
    logc("TX: %s" % tx)
    ser.write(tx)

    rx = ser.read(3)
    logc("RX: %s" % rx)
    if rx != b'OK\r':
        return new_error("Did not get the 'OK' response.")

    return Success


def get_atap(ser: serial.Serial) -> Tuple[int, Optional[Error]]:
    """
    get_atap returns XBee's current ATAP setting. Assumes the device is already in raw AT Command mode.
    """

    tx = b'ATAP\r'
    log("%s: TX: %s" % (func(), tx))
    ser.write(tx)

    rx = ser.read(2)
    log("%s: RX: %s" % (func(), rx))
    if len(rx) != 2:
        return 0, new_error("Response contains incorrect number (%d) of bytes." % len(rx))

    try:
        value = int(rx.strip())   # Convert from byte string to integer.
    except ValueError:
        return 0, new_error("Response did not contain a valid number.")

    return value, Success


def set_atap(ser: serial.Serial, new_mode: int) -> Error:
    """
    set_atap changes the XBee ATAP setting. Assumes the device is already in raw AT Command mode.

    Note that we do NOT invoke a write command so that this change will NOT persist across device resets.
    """
    tx = b'ATAP%d\r' % new_mode
    log("%s: TX: %s" % (func(), tx))
    ser.write(tx)

    rx = ser.read(3)
    log("%s: RX: %s" % (func(), rx))
    if rx != b'OK\r':
        return new_error("Did not get the 'OK' response.")

    return Success


def ensure_api_mode(port: str, baud_rate: int) -> Tuple[int, Optional[Error]]:
    """
    ensure_api_mode Attempts to put the XBee into API Mode Without Escapes.
    If successful, returns the original operating mode so that it can be put back later (see restore_mode).

    Note that we do NOT invoke a write command so that this change will NOT persist across device resets.

    Rationale: This function is useful if you want to run an xbee-python application and you are not sure
    whether the device is already in API Mode. The xbee-python application only supports API Frames.
    Consequently, this function is implemented using PySerial directly, not the xbee-python library.
    """

    with serial.Serial(port=port, baudrate=baud_rate, bytesize=serial.EIGHTBITS,
                       parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                       timeout=1.0, rtscts=False) as ser:

        logc("Attempting to enter raw AT Command mode.")
        err = enter_raw_AT_command_mode(ser)
        if err:
            return 0, wrap_error(err)

        logc("Successfully entered raw AT Command mode.")

        logc("Checking ATAP setting.")
        current_mode, err = get_atap(ser)
        if err:
            return 0, wrap_error(err)

        if current_mode == API_MODE_WITHOUT_ESCAPES:
            logc("Already in API Mode; nothing to be done.")
        else:
            logc("Changing from mode %d to API Mode." % current_mode)
            err = set_atap(ser, API_MODE_WITHOUT_ESCAPES)
            if err:
                return 0, wrap_error(err)

        logc("Exiting out of raw AT Command mode.")
        err = exit_raw_AT_command_mode(ser)
        if err:
            return 0, wrap_error(err)

        return current_mode, Success


def restore_mode(port: str, baud_rate: int, original_mode: int) -> Error:
    """
    restore_mode puts the device back into the given operating mode. Assumes it is already in API Mode.
    Note that we do NOT invoke a write command so that this change will NOT persist across device resets.

    Note that we must implement this directly with PySerial, not with xbee-python, because if  we
    restore the mode from ATAP1 (API Mode Without Escapes) back to ATAP4 (REPL Mode), the xbee-python code
    will time out immediately after issuing the command because xbee-python only supports API Mode, not API Mode.
    """

    if original_mode == API_MODE_WITHOUT_ESCAPES:
        log("Original mode was API Mode Without Escapes. Already in that mode; nothing to be done.")
        return Success

    with serial.Serial(port=port, baudrate=baud_rate, bytesize=serial.EIGHTBITS,
                       parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                       timeout=1.0, rtscts=False) as ser:

        logc("Restoring previous operating mode.")

        restore_mode

        command = b"AP"
        params = bytes([original_mode])
        tx = api_frame_at_command(command, params)

        logc("TX: %s" % tx)
        ser.write(tx)

        expected = b"\x7E\x00\x05\x88\x01\x41\x50\x00\xE5"
        rx = ser.read(len(expected))
        logc("RX: %s" % rx)
        if rx != expected:
            return new_error("Failed to restore previous operating mode. Did not get the expected response.")

        logc("Successfully restored previous operating mode.")
        return Success


def ensure_running_latest_micropython_app(build_dir: str, xbee: XBeeDevice) -> Error:
    """
    Deploys the compiled .mpy files to the target. Also ensures that no main.py file exists on the device.

    Assumes that the xbee device has already been already opened.

    A note about main.py versus main.mpy:
    We compile main.py to main.mpy and deploy the .mpy version to the device.
    Note that if the device already contains a main.py, it will run the main.py instead.
    It is therefore up to the host processor (if one) or else the MicroPython deployment process
    to ensure that no main.py file exists on the device. When I first started using XBees, I deployed
    .mpy versions of all files EXCEPT main.py so that you'd never have a case where you accidentally
    deploy an out-of-date main.py that keeps running at startup instead of your desired main.mpy file.
    But that approach has the following downsides: 1) waste RAM and time at startup because the device
    must compile the .py file every time, 2) more complexity because you need to train main.py
    as a special case, 3) you don't the compile-time checking advantages of cross-compiling main.py
    unless you compile it too. Short answer: Use main.mpy on the device.
    """

    # TODO Make this function also remote any extraneous .mpy file from the device!

    mpy_files = [XBeeFile(file_path) for file_path in glob.glob("%s/*.mpy" % build_dir)]

    updated_files = False  # Indicates if file(s) were updated so that MicroPython interpreter can be restarted.
    main_py_was_deleted = False  # Indicates if main.py was removed so that MicroPython interpreter can be restarted.
    updated_atps = False  # Indicates if the ATPS setting (automatically launch MicroPython code at startup) is set.

    with OpenFileSystem(xbee) as fs:

        # Update any missing or out-of-date .mpy files on the device.
        for f in mpy_files:

            # Test if file needs to be deployed.
            log("Checking SHA-256 hash of the file %s" % f.name)
            f.retrieve_xbeehash(fs)
            if f.xbeehash == f.localhash:
                continue

            # Deploy the file.
            try:
                log("Deploying file %s" % f.name)
                fs.put_file(source_path=f.localpath,
                            dest_path=f.xbeepath,
                            secure=False)
            except FileSystemException as ex:
                return Error("ERROR: Failed to deploy file %s: %s" % (f.xbeepath, ex))

            # Check that file was correctly deployed.
            log("Verifying correct deployment of the file %s" % f.name)
            f.retrieve_xbeehash(fs)
            if f.xbeehash != f.localhash:
                return Error("ERROR: Deployed file checksum mismatch! %s vs %s" % (f.xbeehash, f.localhash))

            updated_files = True

        log("mpy_files:\n%s" % "\n".join(["%s" % f for f in mpy_files]))

        # Ensure that main.py does not exist on the device.
        try:
            fs.remove_element(MAIN_PY)
            main_py_was_deleted = True
            log("Successfully deleted file %s." % MAIN_PY)
        except FileSystemException as ex:
            if "ENOENT" not in repr(ex):
                return Error("ERROR: Failed to delete %s. Details: %s" % (MAIN_PY, ex))
            log("Looks like file %s does not exist. Good." % MAIN_PY)

    # Ensure that ATPS is set to enable MicroPython to run at startup.
    param = "PS"
    desired = b"\x01"
    actual = xbee.get_parameter(param)
    if actual != desired:
        log("AT%s needs to be changed. was %s, changing to %s" % (param, actual, desired))
        xbee.set_parameter(param, desired)
        xbee.write_changes()  # Persist this change across device resets.
        updated_atps = True
        actual = xbee.get_parameter(param)
        if actual != desired:
            return Error("ERROR: Failed to change AT%s setting" % param)
    log("Confirmed that AT%s is set correctly." % param)

    # Determine if the MicroPython interpreter needs to be restarted.
    if updated_files or main_py_was_deleted or updated_atps:
        log("Need need to restart the MicroPython interpreter because %s%s%s" % (
            "one or more MicroPython files changed." if updated_files else "",
            "an old main.py was deleted." if main_py_was_deleted else "",
            "ATPS was not previously set." if updated_atps else ""))
        err = restart_micropython_interpreter(xbee)
        if err:
            return Error("Error: Failed to restart MicroPython interpreter. Details: %s" % err)
        log("Successfully restarted MicroPython interpreter.")
    else:
        log("MicroPython interpreter does not need to be restarted. It is already running the latest code.")

    return Success


def ensure_micropython_is_disabled(xbee: XBeeDevice) -> Error:
    """
    Ensures that ATPS (MicroPython auto start) is disabled. If it was running, it writes the change
    so that it persists across reboots and then restarts the device-- this stops any running MicroPython code
    and won't restart after the reboot because ATPS has been disabled.

    This function is useful if you were running some MicroPython code on the device and now
    you want to instead run some xbee-python based code using the XBee from a PC, and furthermore
    you want to ensure there is no code running on the device that could interfere with your PC app.
    """

    param = "PS"
    desired = b"\x00"
    actual = xbee.get_parameter(param)
    if actual == desired:
        logc("AT%s is already set to the desired value; nothing to be done." % param)
        return Success

    logc("AT%s needs to be changed. was %s, changing to %s" % (param, actual, desired))
    xbee.set_parameter(param, desired)
    xbee.write_changes()  # Persist this change across device resets.
    actual = xbee.get_parameter(param)
    if actual != desired:
        return Error("Failed to change AT%s setting" % param)

    logc("Need to restart the device because AT%s has changed." % param)
    err = restart_micropython_interpreter(xbee)
    if err:
        return wrap_error(err, "Failed to restart the device.")

    logc("Successfully restarted the device.")
    return Success
