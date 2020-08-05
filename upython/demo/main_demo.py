"""
main.py contains the MicroPython code to be run in the XBee 3 Zigbee device.
"""

import io
import utime
import binascii
import sys

from machine import Pin
import xbee


from helpers import ButtonBuffer, invert, MAX_PACKET_SIZE, PACKET_TYPE_LOG

# COORDINATOR_ADDRESS = xbee.ADDR_COORDINATOR
COORDINATOR_ADDRESS = binascii.unhexlify("0013a200417d18ee")


def exception_details(ex):
    """
    exception_details takes a thrown exception object and returns
    a string containing the exception details and the stack trace.

    Rationale: In standard CPython, one would use traceback.format_exc(),
    but Digi XBee MicroPython doesn't come with the traceback module.
    """
    traceback_stream = io.StringIO()
    sys.print_exception(ex, traceback_stream)
    return traceback_stream.getvalue()


def log(msg):
    """
    log transmits the given message via the network in a Log Packet.
    If the message is too big to fit into a single packet, this chunks it up.
    """
    dest = COORDINATOR_ADDRESS
    chunk_size = MAX_PACKET_SIZE - 1  # Minus 1 to make room for the packet type byte.
    for i in range(0, len(msg), chunk_size-1):
        chunk = msg[i:i+MAX_PACKET_SIZE]
        tx = bytes([PACKET_TYPE_LOG]) + chunk
        try:
            xbee.transmit(dest, tx)
        except:
            print(msg)  # Looks like xbee.transmit isn't working, so just use print instead.


def main():
    func = "main"
    try:
        pass   # TODO  your code goes here!
    except Exception as ex:
        log("%s: Fatal exception occurred in main. Details: %s" % (func, exception_details(ex)))


if __name__ == "__main__":
    main()
