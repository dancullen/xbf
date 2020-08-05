# Digi XBee and XBee3 Notes


## Resources
- [XBee Features Chart](https://www.digi.com/pdf/chart_xbee_rf_features.pdf) - Gives part numbers of each EFM32 microprocessor and each modem (Telit or u-blox) for each XBee model number.
- [Digi XCTU User Guide](https://www.digi.com/resources/documentation/digidocs/90001458-13/default.htm)
- [Digi XBee3 Cellular LTE-M/NB-IoT Product Page](https://www.digi.com/products/embedded-systems/cellular-modems/xbee3-cellular-lte-m-nb-iot)
- [Digi XBee3 Cellular LTE-M/NB-IoT Global Smart Modem User Guide](https://www.digi.com/resources/documentation/Digidocs/90002258/)
- [Digi XBee3 + MQTT Tutorial](https://www.digi.com/videos/connecting-digi-xbee3-cellular-to-aws-with-mqtt)
- [Git repo for XBee3 MicroPython](https://github.com/digidotcom/xbee-micropython)
- [Official MicroPython repo's MQTT implementation](https://github.com/digidotcom/xbee-micropython/blob/master/lib/umqtt/simple.py)
- [Sparkfun XBee Tutorial](https://learn.sparkfun.com/tutorials/exploring-xbees-and-xctu/all)
- [XBee3 Hardware Reference Manaual](https://www.digi.com/resources/documentation/digidocs/pdfs/90001543.pdf) - Gives pinouts and package footprints and tips for laying out boards that contain XBee3s, but not much else.
- [XBee Python Library](https://xbplib.readthedocs.io/en/latest/) - Runs on your host system and talks to your XBee over serial via XBee API Mode. It uses PySerial.
- [XBee Terminology](https://xbplib.readthedocs.io/en/latest/user_doc/xbee_terminology.html) - This page is particularly helpful.
- [XBee Cellular Confluence page](https://confluence.digi.com/display/XBEE/)
- [Digi XBee ANSI C Library](https://github.com/digidotcom/xbee_ansic_library) - Library for writing C applications that talk to the XBee over serial via XBee API Mode.
  - [JIRA for XBee ANSI C Library](https://jira.digi.com/projects/XBCLIB/issues)
  - [Internal mirror of the GitHub repo with some private branches](https://stash.digi.com/projects/XBEE/repos/host_ansic_driver/browse)
- [XBIB-U-DEV Schematics](http://ftp1.digi.com/support/images/XBIB-UDevelopment%20board.pdf) And more information can be found on the [Digi-Key page for this product](https://www.digikey.com/short/pmmtw1).
- XBee Mobile SDK
  - [XBee Mobile SDK Confluence Page](https://confluence.digi.com/display/BBEE/XBee+Mobile+SDK) - Managed by the BumbleXBee Team.
  - [XBee Mobile Apps directory in Stash](https://stash.digi.com/projects/XBLE_APPS)
  - [XBeeLibrary.sln can be found here](https://stash.digi.com/projects/XBLE_APPS/repos/xbee_csharp_library/browse/XBeeLibrary.sln)
  - [XBeeConfigurator.sln can be found here](https://stash.digi.com/projects/XBLE_APPS/repos/xbee_ble_configuration/browse/XBeeConfigurator.sln)
- [Tips on updating XBee firwmare and cell radio chip firmware](https://jira.digi.com/browse/CSXB-119)


## Wireless Notes
- NB-IoT encompasses LTE CAT NB1 and LTE CAT NB2. https://en.wikipedia.org/wiki/Narrowband_IoT


## Part Numbers
- [Digi XBee3 Cellular LTE-M/NB-IoT Global Smart Modem](https://www.digi.com/products/embedded-systems/cellular-modems/xbee3-cellular-lte-m-nb-iot)
  - Product Family: XBC3
  - Cellular modem: u-blox SARA-R410M-02B
    - Supports CAT M1/NB1
  - Microcontroller: Silicon Labs EFM32GG395F1024-BGA120 Giant Gecko 32-bit MCU
    - **UPDATE 2019-06-03:** Apparently this is a typo. The older XBee Cellular devices use the EFM, but the newer devices use the EFR chip! Part number: EFR32MG12P432F1024GL125-B
  - This verison of XBee3 allegedly supports Bluetooth Low Energy (BLE) (according to product page) but this functionality is not handled by the u-blox chip, nor is it handled by the EFM32 chip!
    - The user manual for this device states, "Some of the latest XBee3 modules support Bluetooth Low Energy (BLE) as an extra interface for configuration." Dan: So this means some, but not all.
    - When I enabled BT in XCTU for this device and scanned on my phone for new devices, it didn't show up in the list. So I'm pretty sure this module doesn't have Bluetooth.
    - So maybe there is actually a newer, alternate u-blox part number that Digi is using now.
     - **UPDATE 2019-05-13**: Dave found out from Cameron downstairs that the Bluetooth is implemented IN SOFTWARE in the EFM32 in the XBee3 Cellular LTE-M/NB-IoT! So no wonder I didn't see it in the hardware description!
        (And we don't have access to that source code so of course I couldn't find it!)
     - **UPDATE 2019-05-14**: I installed the [XBee3 Mobile App](https://www.digi.com/blog/wireless-configuration-with-the-xbee-mobile-app/) and confirmed that it could see my XBee3 via Bluetooth.
        (I just wasn't able to connect to it because it said the firmware version was unsupported.) But nevertheless, this confirms that this model XBee3 does indeed support Bluetooth.
  - This version of XBee3 does not support Wifi.

- [Digi XBee3 Cellular LTE-CAT1](https://www.digi.com/products/embedded-systems/cellular-modems/xbee3-cellular-lte-cat-1)
  - Cellular modem: Telit LE866A1-NA
  - Microcontroller: EFR32MG12P432F1024GL125-B

- [Digi XBee Zigbee](TBD)
  

## AT Commands Cheat Sheet

If you're going to send AT commands, use the Console in XCTU (Click icon at top right that looks like a computer screen)

```
+++ (wait 1 sec)   # Enter command mode. Note that there is no [CR]!
ATAP4[CR]          # Set mode to MicroPython.
ATAP[CR]           # Check mode.
ATCN[CR]           # Exit command mode. (Or you instead could just wait 10 seconds, which is what the setting CT (Command Mode Timeout) happens to be set to. By default it is 0x64 tenths of a second = 100 tenths = 10 sec)
```

If you're going to write MicroPython, use the MicroPython Terminal instead (because it doesn't echo back /duplicate everything you type).
Access this via "Tools... MicroPython Terminal" by clicking the Tools icon at the top-right in XCTU, as instructed in section
"Use the MicroPython Terminal in XCTU" of the user guide.


## Sending HTTP request with MicroPython

- Download this file: https://github.com/digidotcom/xbee-micropython/blob/master/lib/urequests.py
  (It's the micropython version of the [requests library](https://3.python-requests.org/).
- Transfer to XBee3:
  - File... File System Manager
  - Open the connection to the XBee3.
  - Drag the urequests.py folder from your local machine to /flash/lib/urequest.py on the XBee3.
- Open MicroPython terminal and send this stuff:
  ```
  import urequests
  r = urequests.get("http://api.ipify.org/")
  r.status_code
  r.text
  r.content
  ```

## Invoking AT commands from MicroPython shell

https://www.digi.com/resources/documentation/Digidocs/90002219/#tasks/t_print_at_commands.htm

```
import xbee
x=xbee.XBee()
x.atcmd('VL')  # Print firmware version verbosely
```

## Machine module

```
import machine
machine.soft_reset()
```


## Launching a MicroPython program at device startup

https://www.digi.com/resources/documentation/Digidocs/90002219/#tasks/t_run_code_startup.htm

Set the PS (Python Startup) register to 1. The XBee automatically triest to run /flash/main.py (and then /flash/main.mpy) when the device powers up or resets.



## XBee Modes
- What's the difference between API mode and Transparent mode?
  - See "Modes" section of 90002258.
  - "The XBee Smart Modem interfaces to a host device such as a microcontroller or computer through a logic-level asynchronous serial port. It uses a UART for serial communication with those devices."
  - The diagram under "Select an operating mode" shows the several interfaces:
    - MicroPython REPL
    - Transparent
    - API
    - Bypass.  
  - "MicroPython mode":
    - AP=4
    - "MicroPython mode connects the primary serial port to the stdin/stdout interface on MicroPython, which is either the REPL or code launched at startup."
    - I believe the code in simple.py from https://github.com/digidotcom/xbee-micropython (referenced from the XBee3+MQTT tutorial video) is essentially just a wrapper around Command Mode.
  - "Transparent operating mode":
    - AP=0
    - Dan: Essentially each byte you send to the XBee in Transparent Mode gets transmitted out of the RF data stream of the cellular modem as if you were talking to the remote endpoint over a serial port.
    - "Devices operate in this mode by default."
    - "The device acts as a serial line replacement when it is in Transparent operating mode."
    - "The device queues all serial data it receives through the DIN pin for RF transmission."
    - "When a device receives RF data, it sends the data out through the DOUT pin."
    - "You can set the configuration parameters using Command mode."
    - "The IP (IP Protocol) command setting controls how Transparent operating mode works for the XBee Smart Modem."
    - Dan: According to [this page](https://os.mbed.com/users/dannellyz/notebook/at-vs-api-when-why-how/),
      if you're in transparent mode (sometimes called Application Transparent, or AT mode in older literature--
      not to be confused with "AT" (ATention) commands), no packet information is necessary-- it just sends
      bytes directly to the Desination Address stored in memory. It's the fastest way to get up and running
      (good for newbees) and is easy if you're only communicating with one endpoint.
  - API operating mode":
    - AP=1 or AP=2. (2 means escaped with control characters)
    - "API mode is a frame-based protocol that allows you to direct data on a packet basis."
    - "API mode provides a structured interface where data is communicated through the serial interface in organized packets and in a determined order."
  - "Command mode"
    - Dan: This is where you send AT commands to the XBee!
    - Dan: You can always enter this mode, regardless of what mode you're in, by waiting one second, then sending "+++", then waiting one second.
      - This actually agrees with https://en.wikipedia.org/wiki/Hayes_command_set, which states:
        "When in data mode, an escape sequence can return the modem to command mode. The normal escape sequence
          is three plus signs (+++), and to disambiguate it from possible real data, a guard timer is used:
          it must be preceded by a pause, not have any pauses between the plus signs, and be followed by a pause;
          by default, a 'pause' is one second and 'no pause' is anything less."
    - "Command mode is a state in which the firmware interprets incoming characters as commands.
      It allows you to modify the device’s configuration using parameters you can set using AT commands."
    - Dan: You're communicating with the SiLabs EFM32, which passes data along (as needed) to the Telit/u-blox modem.
  - "Bypass operating mode": 
    - IMPORTANT NOTE: This mode has been deprecated. Use "USB direct mode" instead.
    - "In Bypass mode, the device acts as a serial line replacement to the cellular component.
      In this mode, the XBee Smart Modem exposes all control of the cellular component's AT port through the UART. I"
    - Dan: IN OTHER WORDS, the SiLabs EFM32 is bypassed entirely and you talk directly to the Telit/u-blox cell modem with AT commands via the serial interface.
  - "USB direct mode": "You should use this mode if you want to connect using PPP through the cellular modem while using a host operating system, such as embedded Linux."
    - Dan: If you want to use the XBee's Telit/u-blox cell modem directly, i.e., plugging it directly into a Linux box via USB and bypass the SiLabs EFM32 processor entirely
      and use the Linux PPP driver to make it show up just like any other Ethernet interface.
      - This is known as "USB direct mode"
      - There used to be something called "Bypass operating mode", but that is marked as deprecated.
      - However, you'll still need to select "Bypass Mode" in XCTU (AP=5) to use USB direct mode.
    - Dan: See Rob's document "Configuring an XBee Cellular LTE.docx" for instructions on setting up PPP for use with the XBee3 on Ubuntu systems.
  - Use "+++" within one second to enter command mode. (This is the [escape sequence discussed here](https://en.wikipedia.org/wiki/Hayes_command_set).)

- **For Talis Medical, Rob had to use Bypass mode, NOT USB Direct mode, because Talis' board didn't have any free USB ports.**

- "AT Commands"
  - Some of these go to the cell modem and others are used to configure the XBee3. Such as ATIP, which configures IP socket mode (UDP vs TCP vs SMS vs SSL over TCP).

- "Serial Interface"
  - The XBee interfaces to a host device through a UART at logic level voltages, through a level translator (RS-232 or USB interface board (e.g., FTDI)), or thorugh a SPI port.

- Physical interfaces
  - @todo figure out: You can plug in the USB connection and there's an FTDI chip that provides two serial ports, one used for data and the other used for configuration. But you're still talking through the SiLabs chip.
  - SPI operation
  - serial
  - USB / FTDI
  - See "Hardware... Pin Signals" in the Digi XBee3 Ceullular LTE-M/NB-IoT Global Smart Modem User Guide.

- What's the difference between USB Direct and Bypass mode?
  - USB Direct uses pins 7 and 8 on the XBee3 to talk directly to the Telit or u-blox chip.
  - Bypass mode uses the serial interface (pins 2 and 3 on the XBee3), to send bits to the chip unmodified,
    but it's still going through the EFM32 processor and it's still checking the stream for the escape sequence (pause+++pause).
  - USB Direct mode is preferred. Bypass mode deprecated. With USB direct mode, there's no EFM32 processor in the middle.
  - Another limitation of Bypass mode: It doesn't implement UART flow control, as explained in the manual on the page "Hardware flow control in Bypass mode".

- What's the difference between Transparent and Bypass modes?
  - Transparent mode sends bytes to the remote endpoint (across cellular network) as if the XBee is just a data pipe to the destination-- it sets up the sockets and things for you.
  - Bypass mode allows you to send bytes directly TO the cellular modem (e.g., AT commands), rathern than THROUGH the celluar modem, so that you can control it directly.
  - But USB direct mode is preferred to Bypass mode because the traffic doesn't go through the EFM32 chip on its way to the cellular modem.
  - In Bypass mode, you are essentially bypassing the EFM32 chip and talking directly to the cellular modem.
    Of course, that's not quite true because the bits still go through the EFM32, and in fact, you can still send the escape sequence (pause+++pause) to return to command mode.
    But as far as the data goes, it's mostly just going straight to the cellular modem without modification.

- What does the [simple.py](https://github.com/digidotcom/xbee-micropython/blob/master/lib/umqtt/simple.py) MQTT library (on Digi's GitHub) do?
  Answer: It packs bytes in [MQTT format](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html).
  In other words, this file implements the MQTT protocol. So this protocol is implemented in MicroPython.

- The XBee3+MQTT video shows how to use XCTU to configure the device. It suggests 115200 baud, MicroPython REPL mode (AP=4).

- Throughput? 115200 bits/sec * 1 byte / 10 bits (includes parity and stop) = 11,520 bytes per second ... / 1024 = 11 kBytes per second = 0.01 MBytes/sec ... which is pretty terrible.

- Dan: It sounds like the SPI interface has many limitations and is not recommended.
  - "You cannot use the SPI interface to enter Command mode."

## Connecting to Digi Remote Manager (DRM)
- How do devices securely connect to DRM?
 - Question? Any certificates that need to be installed?
   - Answer: See section "Secure the connection between an XBee and Digi Remote Manager with server authentication" in the "XBee3 Cellular LTE-M/NB-IoT User Guide".
     Apparently you need to set up some certificates. But if you have XBee firmware version x11 or later, the certificates to secure the connection to DRM are installed by default. Yay.
   - Aside: I'll bet the Connect Sensor already contains all these certificates (since it's meant to work with DRM right out of the box) which is why I didn't have to set those up for the Connect Sensor.
 - Are there any settings changes that you must make in XCTU?
   - Answer: Ensure that the following settings are in effect:
     - DO (Device Option) register Bit 0 must be set. (This enables the use of DRM within the firmware).
     - MO (Remote Manager Options) register Bit 1 must be set. (This enables TLS for the Remote Manager TCP connection.)
       - UPDATE 2019-06-10: Note that the "MO" and "DF" options appear to be only available in the latest version
         of the XBee3 Cellular LTE-CAT1 firmware (v31011); these features are unavailable in the previous version (v31010)!!!
         And similarly, for the XBee3 Cellular LTE-M/NB-IoT, you need the newest firmware (v11411); they are unavailable in v11410!!!
         Furthermore, it appears that using TLS is now the default setting. So they must be trying to phase out the unsecured TCP port.
     - $D (SSL/TLS Certificate File) must be set. By default it points to ```/flash/cert/digi-remote-mgr.pem```. This tells the firmware where to look for the certificate file to use.
   - Tip: For testing, the recommended way to force an active connection to Digi Remote Manager is to set Bit 0  ("Always remain connected through TCP") in the MO register.
     - Other relevant settings are K2 (Device Send Keepalive Interval) and DF (Remote Manager Status Check Interval).
     - Tip: I had to power-cycle the device (unplug USB and plug back in) before it tried to connect to DRM.
     - Status is also reported in the DI (Remote Manager Indicator) register.
 - Question: What prevents devices from spoofing their IMEI?
   - You add their IMEI number to DRM, but can't that be spoofed?
     Can't you make your device pretend to be another device and push false data to another user's account??
   - Answer: @todo figure this out!

## Digi Remote Manager (DRM) API
- Appears to be an XML-based API.
- Digi calls its DRM API the "SCI" (Server Command Interface).
- "SCI is available only in Premier Adeition accounts". (According to the Remote Manager Programmer Guide).
- See "Update the firmware using web services in Remote Manager" section in "XBee3 Cellular LTE-M/NB-IoT User Guide" for a few examples that use Python to hit the API.

## Sleep Modes
How do we put the XBee3 to sleep? What are the low power modes?
- airplane mode vs [deep] sleep.
- See "sleep modes" section of hte user guide.
- normal mode (not sleeping)
- pin sleep -- pin `SLEEP_RQ` (pin D8) manages sleeping
- cyclic sleep
- cyclic sleep with `SLEEP_RQ` (pin D8) wakeup.
- When `SLEEP_RQ` is high, it tells the device to enter low-power mode. When it is low, it tells the device to come out of low-power mode.

How much power does the device use?
See "Power consumption" section of "XBee3 Cellular LTE-M/NB-IoT User Guide".
- Active (normal) mode current (idle/connected, listening): 20 milliAmps
- Power save mode current: 20 microAmps (what is this? airplane mode?)
- Deep sleep current 10 microAmps (what is this? sleep mode?)
- According to the [product page](https://www.digi.com/products/embedded-systems/cellular-modems/xbee3-cellular-lte-m-nb-iot#specifications):
  - SUPPLY VOLTAGE: 3.3-4.3VDC
  - PEAK TRANSMIT CURRENT: 550mA w/ Bluetooth disabled; 610mA w/ Bluetooth enabled
  - AVG TRANSMIT CURRENT (LTE-M): 235mA
  - AVG TRANSMIT CURRENT (NB-IoT): 190mA
  - POWER SAVE MODE: 20uA
  - DEEP SLEEP: 10uA

How does this power usage compare to the Connect Sensor power usage?
- The "Connect Sensor User Guide" isn't clear.
- But according to the [product page](https://www.digi.com/products/networking/gateways/digi-connect-sensor#specifications),
  - BATTERY AND BATTERY LIFE: 7.2 V, 14.5 Ah, Lithium thionyl chloride, non-rechargeable, replaceable; Approximately 2 years (@ 2 reads/transmits per day)
  - POWER DRAW, SLEEPING: 86.4 uW
  - POWER DRAW, CONTINUOUS MONITOR: 400 mW
  - POWER DRAW, PEAK TRANSMIT: 14.4 Watts

So what does the comparison look like
- Dan: At 3.3V, 10uA translates to P = IV = 3.3V times 10 uA = 33 uW
- And if the rest of the Connect Sensor draws 86.4 uW in sleep... So the XBee3 draws almost half the power (before integrating it) as the ConnectSensor.
- But how much does the Telit modem draw in sleep mode? Because if we nopop the Telit modem, how much power do we save?

Telit LE910-SV1 cellular modem power consumption
- See section 4.2 Power Consumption of https://www.telit.com/wp-content/uploads/2017/09/Telit_LE910_V2_Hardware_User_Guide_r9.pdf
- Switched off: Draws 95 uA
- IDLE mode: 13 mA (LTE)
- Supply requirements: Nominal supply is 3.8V (per Section 4.1).
- 95 uAmps * 3.8 V = 361 uW
- 13 mA * 3.8 V  = 49 mW

Hmmm... I'm not sure where this leaves us.


# XBee Zigbee
- [XBee/XBee3 Cellular Source Code](https://stash.digi.com/projects/XBEE/repos/cellular/browse)
  - Cloning: ```git clone ssh://git@stash.digi.com/xbee/cellular.git --recursive```
  - Note the ```--recursive``` flag to also pull in submodules.


# Checking if an XBee is connected.

- The ATAI command returns a code that tells you what the XBee connection status is.
  - See the sample code snippet on [this page](https://www.digi.com/blog/hands-on-micropython-programming-examples-for-edge-computing-part-2/)
    which recommends defining the following snippets for interpreting the value:
    ```
    ai_desc = {
    0x00: 'CONNECTED',
    0x22: 'REGISTERING_TO_NETWORK',
    0x23: 'CONNECTING_TO_INTERNET',
    0x24: 'RECOVERY_NEEDED',
    0x25: 'NETWORK_REG_FAILURE',
    0x2A: 'AIRPLANE_MODE',
    0x2B: 'USB_DIRECT',
    0x2C: 'PSM_DORMANT',
    0x2F: 'BYPASS_MODE_ACTIVE',
    0xFF: 'MODEM_INITIALIZING',
    }
    ...
    print("ATAI=0x%02X (%s)" % (new_ai, ai_desc.get(new_ai, 'UNKNOWN')))
    ```
  - [This page](https://www.digi.com/resources/documentation/Digidocs/90002258/#Reference/r_cmd_AI.htm) defines these values.


# MQTT Client Authentication
- https://docs.aws.amazon.com/iot/latest/developerguide/iot-security-identity.html
  - "TLS client authentication is used by AWS IoT to identify devices"
- https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Enhanced_authentication
  - Dan: MQTT supporters some authentication modes, separate from tls handshake.
    I would say this is analogous to HTTP Basic authentication or API authentication tokens.
    Or like how you can enter username and password on gmail.com login page.
- So which type of authentication Amazon AWS using? I believe it is the former (TLS client authentication),
  due to what the Amazon IoT docs link above says. And also because umqtt/simple.py from the xbee-micropython repo
  doesn't seem to pack any password or x.509 certainly into the MQTT packet.

# Notes about connecting XBees to DRM

  - XBEES DO NOT AUTOMATICALLY CONNECT TO DRM AT POWERUP!!!

  - XBee3s come by default with the TLS enabled for DRM by default.

  - XBee3s don't come with the DRM certificates installed.
    So by default, they will use TLS for encryption with DRM,
    but they won't be able to do any server authentication.
    In other words, the XBee will be able to connect to DRM,
    but it will just be blindly trusting that the DRM server
    is who it claims to be.

  - Note that you can check the register DI to see whether
    server authentication was successful or not.

  - Question: How do we enforce server authentication?
    In other words, is it possible to prevent it from connecting
    to DRM if server authentication fails?

    Note that the register DO is what you use to enable TLS,
    but there is not a bit in register DO to enforce server
    authentication-- it will still connect to DRM, using
    TLS only for encryption, not for authentication.

    I have not been able to find any other registers
    with settings for enforcing server authentication.

    Maybe if you've saved a DRM certificate file to the device,
    it is smart enough to enforce server authentication?
    I dunno, this is just speculation. I have not yet been
    able to find any documentation that describes this very well.
    The best resource is the XBee3 Cellular User Guide link below.

  - For more information on TLS connections to DRM, see:
    https://www.digi.com/resources/documentation/digidocs/90002253/default.htm#Containers/cont_RM_TLS_connection.htm

  - Question: So how do we force the XBee to connect to DRM when it wakes up?
    - Option 1: Set Bit 0 in the MO register to force it to always remain connected to DRM via TCP.
    - Option 2: Set the DRM update interval to somethine like once per minute.
    - But options 1 and 2 are stupid options. Maybe the thing to do is to just let the XBee handle
      its own timing. Set the DRM update interval settings to something sensible.
      And I imagine that once the DRM update timer expires, it wakes up the XBee if it were sleeping,
      and then sends the update to DRM.
    - Another option would be using MicroPython code to control all the timing.
      Oh wait-- never mind, that wouldn't work because there do not exist any
      MicroPython functions that you could use to force a DRM connection.
