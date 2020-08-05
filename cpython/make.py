"""
make.py contains code for cross-compiling .py into .mpy files and for deploying them to an XBee 3 device.
"""

import argparse
import sys

from digi.xbee.devices import Raw802Device

from xbf.cpython.core import Error, Success
from xbf.cpython.core import ensure_api_mode, restore_mode, OpenXBeeDevice
from xbf.cpython.core import log, build_mpy, ensure_running_latest_micropython_app


SRC_DIRS = ["upython", "deps/xbf/upython"]
BUILD_DIR = "build"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="make.py handles compilation and deployment of .mpy files.")

    parser.add_argument("--build", required=False, action="store_true", default=False,
                        help="Cross-compiles the .py files to .mpy files.")

    parser.add_argument("--deploy", required=False, action="store_true", default=False,
                        help="Deploys the .mpy files to the local XBee device.")
    parser.add_argument("--deploy-remote", required=False, action="store_true", default=False,
                        help="Deploys the .mpy files to remote XBee device(s).")  # TODO FIX ME; see comment below.

    parser.add_argument("--apply-profile", required=False, action="store_true", default=False,
                        help="Deploys the .xpro file to the local XBee device.")
    parser.add_argument("--apply-profile-remote", required=False, action="store_true", default=False,
                        help="Deploys the .xpro file to the remote XBee device(s).")  # TODO Fix me; see comment below.

    # TODO Need to update some of the above flags because I've learned more about what's possible/not possible:
    #   - Rename the --deploy-remote flag. It's not possible to deploy .mpy files to a remote XBee device via
    #     the zigbee protocol. However, you can deploy an entire 'ota' filesystem image. So rename the flag
    #     to "--deploy-remote-ota-image"
    #   - Delete the "--apply-profile-remote" flag because it's not possible to deploy an entire .xpro file to
    #     a remote XBee. The best you can do is piecemeal-- you can update firmware of a remote device, then you
    #     can manually update all of the registers of a remote device, and you can also send an 'ota' filesystem
    #     image to a remote device. So we should create separate flags for each of these operations, e.g.,
    #     "--deploy-remote-firmware, "--deploy-remote-settings", and "--deploy-remote-ota-image".
    #
    # TODO
    #   - Implement deploying .xpro files to local device and .ota files to remote devices!
    #     - Aside: It doesn't appear that profiles can be deployed remotely.
    #       https://xbplib.readthedocs.io/en/latest/api/digi.xbee.profile.html
    #   - Implement --profile option that deploys profile
    #     https://xbplib.readthedocs.io/en/latest/examples.html?highlight=profile#profile-samples
    #   - Implement --remote option that deploys filesystem image to remote xbee
    #     https://xbplib.readthedocs.io/en/latest/api/digi.xbee.filesystem.html#digi.xbee.filesystem.update_remote_filesystem_image
    #     https://xbplib.readthedocs.io/en/latest/api/digi.xbee.firmware.html?highlight=filesystem#digi.xbee.firmware.update_remote_filesystem
    #   - Here's the notes from xctu on how to create the ota filesystem image
    #     https://www.digi.com/resources/documentation/digidocs/90001458-13/default.htm#task/t_update_remote_devices.htm?Highlight=ota
    #   - Note that the ATFK register needs to be set ahead of time, because filesystem images are signed.
    #   - It doesn't appear xbee-python supports generating remote filesystem images.
    #     And it doesn't look like there is an xctu option either.
    #     https://www.digi.com/resources/documentation/digidocs/90001458-13/default.htm#concept/c_perform_tasks_by_command_line.htm%3FTocPath%3DUse%2520the%2520XCTU%2520command%2520line%7C_____0

    # Serial port and baud rate are not required for --build, so set required=False and enforce below.
    parser.add_argument("--port", required=False, type=str, default=None,
                        help="Serial port name (e.g., /dev/ttyUSB0 or COM3).")
    parser.add_argument("--baud", required=False, type=int, default=None,
                        help="Serial port baud rate (e.g., 115200).")

    args = parser.parse_args()

    # Additional checks beyond the basic validation performed in parse_args.
    if args.deploy or args.deploy_remote:
        if args.port is None or args.port == "":
            parser.error("--port is required for deployment")
        if args.baud is None or args.baud == "":
            parser.error("--baud is required for deployment")

    return args


def main() -> Error:

    args = parse_arguments()

    if args.build:
        log("Building .mpy files...")
        err = build_mpy(src_dirs=SRC_DIRS, build_dir=BUILD_DIR)
        if err:
            log("Failed to build .mpy files. Details: %s" % err)
            return Error()
        log("Build .mpy files succeeded.")

    if args.deploy:
        log("Deploying .mpy files...")

        original_mode, err = ensure_api_mode(port=args.port, baud_rate=args.baud)
        if err:
            log("Error: Failed to enter API Mode! Details: %s" % err)
            return Error()

        with OpenXBeeDevice(xbee=Raw802Device(port=args.port, baud_rate=args.baud)) as xbee:
            err = ensure_running_latest_micropython_app(build_dir=BUILD_DIR, xbee=xbee)
            if err:
                log("Error: Failed to deploy .mpy files. Details: %s" % err)
                return Error()
            log("Deploy .mpy files succeeded.")

        err = restore_mode(port=args.port, baud_rate=args.baud, original_mode=original_mode)
        if err:
            log("Error: Failed to restore original operating mode! Details: %s" % err)
            return Error()

    if args.deploy_remote:
        log("NOT IMPLEMENTED YET!")
        return Error()

    return Success


if __name__ == "__main__":
    exit_status = main()
    sys.exit(0 if exit_status is Success else 1)
