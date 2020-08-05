# MicroPython.md


# Differences between standard MicroPython and Digi XBee MicroPython

Note that the Digi XBee version of MicroPython differs slightly from standard MicroPython
as follows (not an exhaustive list):
- The ussl module has a slightly different interface (takes keyfile/certfile/ca\_certs arguments,
  which is similar to the standard CPython3 ssl module).
- The Digi XBee3 Cellular MicroPython interpreter ships with several XBee-specific
  built-in modules, namely `cellular`, `digi.cloud`, `machine`, and `xbee`.


# Third-party sources

We obtained the following files from the following locations:

- app/umqtt.py from https://github.com/digidotcom/xbee-micropython/blob/master/lib/umqtt/umqtt/simple.py @d73ff7e00ab9ee05eb3ab2dc672032f226dda1cc


# Known issues and workarounds


## Always, always, ALWAYS plug the XBIB-U-DEV board into AC power!!

- You should plug it in to wall power all the time!
- You won't be able to reliably communicate with the Cat 1 version over serial (XCTU will give strange connection aborted issues).
- You can communicate with the LTE-M/NB-IoT version over serial just fine. And simple TCP requests will probably work just fine.
  But TLS TCP requests will fail with `[Errno 7005] EIO` because TLS requires much more CPU power, which draws just enough
  power to make the device brown out!
- SO JUST USE THE DARN WALL WART!!!
- This also explains why socket.receive() sometimes returns no bytes. Because the thing is browning out.


## Using the XBee3 Cellular with AWS

Start here:
- https://github.com/digidotcom/xbee-micropython/blob/master/samples/cellular/aws/README.md
- https://www.digi.com/resources/documentation/digidocs/90002219/#container/cont_aws.htm

"You can find the host and region for your Rest API Endpoint by clicking on Interact when looking at your Thing in the AWS IoT Console." (from xbee-micropython/samples/cellular/aws/README.md)

You use the same AWS Endpoint for both HTTPS and MQTT
- The Thing Shadow URI gives you access to the REST API that allows you to see cloud cache or "shadow" of the latest data from your AWS Thing.
  https://docs.aws.amazon.com/iot/latest/developerguide/what-is-aws-iot.html
- Example URI for HTTPS / REST API: `xxxxxxxxxxxxx-ats.iot.us-east-2.amazonaws.com`
- There are special topics that AWS defines that allow you to query or set various data for your AWS Thing.

Note that you use different ports for HTTPS and MQTT.
- HTTPS: TCP port 8443
- MQTT: TCP port 8883

There's an issue in which the XBee3 Cellular LTE CAT 1 does not support AWS endpoints that end in "-ats".
You MUST remove the "-ats" part from the AWS Endpoint string; otherwise MicroPython code raises
the exception `[Errno 7111] ECONNREFUSED`. I confirmed this 2019-06-18.

However, you MUST include the "-aws" for the XBee3 Cellular LTE-M/NB-IoT device.
Otherwise MicroPython code raises the exception `[Errno 7005] EIO`.
I confirmed this on 2019-10-24 with firmware version 11413.

In summary:
- For the XBee3 Cellular LTE CAT 1, you must use the format  b'xxxxxxxxxxxxx.iot.us-east-2.amazonaws.com'
- For the XBee3 Cellular LTE-M/NB-IoT, you must use the format  b'xxxxxxxxxxxxx-ats.iot.us-east-2.amazonaws.com'

Relevant JIRAs:
- https://jira.digi.com/browse/XBCELL-4760
-  https://jira.digi.com/browse/XBPY-283

Additional remarks:
- ATS stands for Amazon Trust Services-- it's their latest authentication infrastructure.
  Removing the "-ats" from the AWS endpoint string causes the device to use the legacy (non-ATS) authentication server.
- Note that you use the same version of the root CA file (aws.ca) for both flavors of XBee3 Cellular,
  and you should be using the version of aws.c that has been signed by "Starfield Technologies, Inc."
  as recommended in the Digi MicroPython User Guide.

For more information about Amazon Trust Services (ATS), see:
- https://docs.aws.amazon.com/general/latest/gr/rande.html
- https://www.amazontrust.com/repository/
- https://aws.amazon.com/blogs/security/how-to-prepare-for-aws-move-to-its-own-certificate-authority/


# Space Savings

Heap space fills up very quickly. To save space, we'll need to:

1) byte-compile .py to .mpy and upload the .mpy files to the device.

   SECURITY CAVEAT: Except we'll leave main.py as a .py file.
   The reason is that main.py takes precedence over main.mpy,
   so we want to use main.py to ensure that we have control
   over what is actually going to be executed.

2) Use os.bundle() to copy .mpy files into internal flash.

   We'll have some code inside main.py for checking and handling this at startup.

More details about XBee flash memory capacity can be found here: https://www.digi.com/resources/documentation/digidocs/90002219/#concepts/c_space_allocated.htm


# Memory usage tricks

```
>>> import gc
>>> gc.mem_free(), gc.mem_alloc()
>>>
>>> import micropython
>>> micropython.mem_info()
>>> micropython.stack_use()
```


# Misc tricks

Show all available built-in modules:
```
help('modules')
```

Show all error codes:
```
>>> import uerrno
>>> print(uerrno.errorcode)
```


# os.bundle demo

Setup: First I compiled `urequests.py` to `urequests.mpy` and then copied it to the device (under `/flash/urequests.mpy`).

Prior to bundling:
```
>>> import gc
>>> gc.mem_free(), gc.mem_alloc()
(31568, 432)
>>> import urequests
>>> gc.mem_free(), gc.mem_alloc()
(27184, 4816)
```

Doing the bundling:
```
>>> import os
>>> os.bundle()
[]
>>> os.bundle('urequests.mpy')
bundling urequests.mpy...2188 bytes of raw code
Used 32/371 QSTR entries.
stack: 984 out of 3584
GC: total: 32000, used: 7168, free: 24832
 No. of 1-blocks: 103, 2-blocks: 91, max blk sz: 45, max free sz: 1550
Embedded 1 module(s) to 2486/31152 bytes of flash.
soft reboot
```

After bundling:
```
>>> import gc
>>> gc.mem_free(), gc.mem_alloc()
(31568, 432)
>>> import urequests
>>> gc.mem_free(), gc.mem_alloc()
(30512, 1488)
```
