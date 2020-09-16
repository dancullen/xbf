# Best Practices


## Sort this -- came from an email

I had no idea qstr_info() and mem_info() could provide all that information!

Attached is the code (see upython/bundle_demo.py) that handles the bundling. A few remarks:

•	The function that handles the bundling & re-bundling is called rebundle_if_ncessary(). The code further down in bundle_demo.py demonstrates how to invoke it.

Please note that bundle_demo.py code will not run in its current form! It depends on some other source files such as components.py, which I’ve omitted (sanitizing things from another project). I’m providing this as a reference to give you some ideas about how to structure things. This structure has worked pretty well for me. 

•	The rebundle_if_necessary() function takes a ‘logger’ parameter, which is just a class with a print function to write log messages to various sinks. I pass in the logger as a parameter (dependency injection) to decouple this function from the log sink. The two classes UserDataRelaySinkLogger and DualSinkLogger demonstrate writing logs to various sinks.

•	Sending log messages via user data relay frames is a helpful trick if you have a microcontroller (e.g., ESP32) hooked up over serial and you want the microcontroller to capture and report log output from the XBee’s MicroPython code. The reason I’ve prepended the byte CSXB_LOG_MSG (0x00) to the user data relay packet is because I wrote a custom protocol on top of user data relay frames, and CSXB_LOG_MSG is just the name I assigned to that particular type of message (CSXB was the name of our device). The code in the microcontroller receives user data relay messages, checks the message type of our CSXB protocol, and processes it accordingly.

•	The ENABLE_BUNDLE_FEATURE flag is just a hack I added to enable/disable the bundling feature temporarily while I was experimenting. You can probably remove that check completely. There’s a lot that you can strip out of this function, such as the logger and all the comments.

•	There’s not any particular technical reason why I chose djb2 as the hash algorithm. I just happened to see it being used for something else and it was easy to implement.

•	You’ll see many comments in rebundle_if_necessary() explaining the limitations and pitfalls I encountered with bundling. For example, if you’re not careful, you could fall into a pattern where the bundle will fail and the micropython interpreter will keep restarting and you’ll get into an endless cycle of restarts. (The restarts occur because because os.bundle(files) restarts the interpreter after adding new files, even if a failure occurs.) What’s worse is that the interpreter restarting can somehow interferes with XCTU’s ability to transfer files to the device. That means that when you open up XCTU’s File Manager, it will show missing files or it will fail when you attempt to deploy new files, because the MicroPython code is caught in that strange restart loop. 

You’ll see a commented-out while-loop in rebundle_if_necessary() that causes the code to block in a loop at one spot rather rebundling & restarting. The problem is that it is hard to detect when there is a problem with the bundle (because os.bundle() doesn’t do a good job reporting errors, as I mentioned before), and so I commented it out.

Anyway, in order to break out of the endless cycle of restarts, you’ll have to either press Ctrl+C in the REPL terminal or disable Python auto-run by setting register “PY” to zero. Then you can load the new .mpy files onto the device and hope you’ve fixed the problem.

Very annoying! And it can take a while to realize what’s happening, especially when you’re working in API Frames mode and you don’t have that REPL terminal open to see all the prints from re-bundling & restarting.

•	Another function I found handy during development was delete_any_dot_py_files() (see bundle_demo.py). See the its code comments for more rationale/explanation. You won’t need it if you’re careful not to deploy any .py files by accident, but I think it’s a trick worth knowing about. 

•	You can ignore the ButtonBuffer class and the invert() and sequence_more_recent() function. It’s not relevant to bundling but I didn’t want to take the time to strip it out.

The attached upython/main.py file demonstrates a couple more handy tricks. The function log() shows how to send log messages over a Zigbee network. The function exception_details() gives you a stack trace when an exception occurs.

The function detect_platform() in upython/helpers.py shows how you can detect the device type at runtime. You might find that more convenient than having to manually change the “k.CELL” flag for each device. I’d suggest running detect_platform() once at startup, then caching the result in “k.CELL” to avoid the overhead of invoking this function repeatedly.

I’ve also attached my script (make.py) for with cross-compiling .mpy files and deploying them to the device. There’s also a Makefile that gives some convenient targets for setting up your workspace (virtual environment) and invoking the make.py script. I still need to do a bit of work to generalize some things, rather than hard-coding them, such as COM port name and XBee type (right now it’s Raw802XBeeDevice rather than ZigbeeDevice or CellularDevice). I can send you improvements as I make them. The ‘upython’ and ‘cypthon’ folders contain a few dependencies. In general, the ‘upython’ folder is where I stick my MicroPython .py files and the ‘cpython’ folder is where I stick the .py files that run on the PC (since the standard implementation of Python interpreter is called CPython).

When we spoke last week, I mentioned structuring your MicroPython code in such a way that you could run it on a PC using the the standard CPython interpreter, before testing the code on the device. This speeds up development and allows you to write unit tests. The question is, how can you achieve this? Take a look at the code in the ‘fakes’ directory. There are CPython implementations I wrote for each of the MicroPython libraries. If your MicroPython code requires the ‘usocket’ library, you can now run it on the PC. The PC version imports my version of ‘usocket.py’ (since CPython doesn’t have a ‘usocket’ module). My ‘usocket.py’ file translates between MicroPython’s interface to the standard CPython ‘socket’ module’s interface. Note that I have NOT attached a full-fledged example of this in practice— the script ‘test.py’ only contains very basic unit tests that don’t leverage these mocks/fakes/adapters. But I can send you some examples of that later. I’m still pulling things out of another project, into a format suitable for sharing.

Side note: It’s actually possible to run an x86 build of a MicroPython interpreter on your PC, but I found that it lacked many things like full networking support. And it also lacks the digi-specific stuff calls like ‘cloud.digi’ and ‘os.bundle’. So instead I like to run MicroPython code in CPython on the PC. The language differences are minor enough that it works out great. Just fake/mock anything that your MicroPython code needs.

The nice thing about my version of usocket.py is that you get real network connectivity (to DRM or the Azure MQTT server or wherever you need to go) via CPython’s sockets. Alternatively, you could re-implement usocket.py that sends back canned responses (perhaps better for unit testing, since it avoids having to have your cloud environment set up.) But I find my version of usocket.py to be more useful for development. Another nice thing about my usocket.py: The source code comments point out all the discrepancies between MicroPython’s ‘usocket’ API and CPython’s ‘socket’ API. Ok, that’s enough bragging about usocket.py for now.

More recently, another technique I’ve used (but not shown in the attached sources) is re-implementing some of the calls like xbee.transmit() to use xbee-python under the hood. For example, in cpython/fakes/xbee.py, you can write a transmit() function with the same signature as xbee.transmit() on the real device. Inside your transmit(), you’d put the calls to the xbee-python library for Zigbee transmission. Then you connect an XBee to your PC and put it in API Frames mode. When you call invoke the transmit() function from your PC, xbee-python sends the correct API Frames over serial to the device, causing the device to send the Zigbee packets. This technique has the advantage that you can send real Zigbee packets to real devices (and get real responses if you re-implement receive()), rather than having to fake all the data. This technique still has the advantage of fast turn-around time--  no need to deploy MicroPython files to the device. You can get all the core logic of your app working this way, then when you’re happy with it, deploy the MicroPython files to the device for an integration test on the real hardware.


## Sort this -- email about DRM


Since you want your device to be able to respond to user input (from the mobile app) immediately, I think it makes sense to keep the connection to DRM open as you’re currently doing (i.e., enable “MO” Bit 0). Furthermore, keeping the connection open (rather than frequent closing and reopening) allows you to conserve mobile data usage because the TLS handshake at the start of the connection requires a nontrivial amount of data that can add up quickly.

In order to keep the connection alive, the client and server periodically send keep-alive messages, which prevent other side from timing out / hanging up. The keep-alives also prevents the service provider from terminating a connection presumed to be inactive.

The main thing I suggest is increasing the values of the keep-alive registers, K1 and K2, from the default values (75 sec and 60 sec, respectively) to 15 minutes each. We typically recommend 15 minutes to our cellular gateway customers because it saves quite a bit of data but still works well with all major carriers— they don’t provide specifications for the timeout but we have not seen a connection terminated when using a 15-minute keep-alive. 

I’m not sure why the XBee’s factory defaults aren’t already set 15 minutes. Maybe they wanted to make darn sure that new customers wouldn’t have any problems with terminated connections. Or maybe 60 seconds and 75 seconds were just an arbitrary initial choice that no one questioned.

The keep-alives might not seem like much, but even a 60-second keep-alive can amount to tens of MB of data usage per month. The reason is since the keep-alives are sent over the TLS connection, the padding / overhead of encryption adds several KB per message. I’m not advocating to disable encryption. TLS security is absolutely essential these days. I’m just pointing out that we need to limit the number of transmissions.

That same idea applies to publishing metrics and other pieces of information. It is more efficient to better to batch up larger chunks of data and send them out at once, packed into in fewer TCP segments, rather than sending lots of smaller TCP segments.

If you’re familiar with how TCP works, you may wonder where the TCP keep-alive feature fit into this. Since TCP keep-alives are handled within the TCP layer, they do not incur the overhead of TLS encryption. However, the XBee 3 LTE-M’s TCP stack doesn’t seem to implement TCP keep-alives, so this is not an option for us. (In contrast, I believe the Digi cellular gateway products give the user some control over the TCP keep-alives.) It’s also worth pointing out that since the Remote Manager protocol already sends its own keep-alives, the lower-level TCP keep-alives are redundant and unnecessary.

I gave some thought to perhaps keeping the DRM connection closed but still listening on a given TCP or UDP port for requests, and then only opening the DRM connection when a request comes in. That way, the DRM connection would only be active when a user is actively interacting with the mobile app. However, the short answer is that there’s not a well-established path to doing this (even DRM’s “Request Connection” feature requires the device to poll the server for the queued request). So the best option is  to stick with the current design and keep the DRM connection open.

As far as publishing the signal strength metric is concerned, your approach in drm.py using cloud.device_request_received() is very reasonable. There are other ways to publish signal strength (the “HM” and “HF” registers come to mind), but since you have other metrics you want to publish, a custom protocol over device_request / SCI  is not a bad idea. Are the metrics something that you only send back upon request, or do you also want periodic reports of signal strength (perhaps hourly updates so you can see a historical graph of uptime in the app)? Obviously mobile data usages are a big constraint. I can think of a couple other options for publishing data values to DRM, but it might be easier to talk through all of this on the phone.

It’s also probably worth having a discussion about whether you really need DRM. For example, you could publish the data directly to Azure using MQTT (e.g., umqtt.py, which I’ve used quite a bit) or a REST API. You’d probably still want to use DRM for deploying firmware updates (and updates to the MicroPython app), but I’d be happy to explain the alternatives. I really wish there was a stand-alone microservice that you could host yourself that pretends to be DRM and serves up firmware images the same way  as DRM. I think firmware updates are probably the most valuable feature that DRM provides. If you’re going to use DRM, you might as well use the digi.cloud library too because it’s fairly convenient (it’s built in) and it’s pretty efficient on the data. 


## Sort this-- notes on firmware downloading

Your host microprocessor can program the new XBee 3 Zigbee firmware image via the serial port. Programming the firmware over serial is essentially just an XMODEM-CRC file transfer. In fact, this is the technique that XCTU uses to update the XBee firmware. (One time I confirmed this by sniffing the serial bytes while using XCTU to update some firmware.)
 
If your host microprocsesor doesn’t have enough space to store the entire XBee 3 Zigbee image, you could probably download a chunk of the image at a time and then send each chunk out the serial port as soon as you receive it. In fact, I was experimenting with this approach just a few weeks ago—I wrote some MicroPython code for an XBee 3 Cellular to update the firmware on an XBee 3 Zigbee, where the two devices are connected together via their serial ports. (Haven’t quite finished yet, but I did get the XMODEM-CRC code working.)
 
In order to initiate the XMODEM-CRC file transfer, you need to invoke the XBee 3 Zigbee’s bootloader. This page from the XBee 3 Zigbee User Guide explains how to do that: https://www.digi.com/resources/documentation/digidocs/90001539/#concepts/c_xbee_bootloader.htm In the past (for older XBees and older XBee 3 firmware versions), this used to be a bit tricky— you had to reset the device, assert DTS and/or RTS, change the baud rate, etc. But they recently added the “AT%P” command that makes it very easy to drop into the bootloader.
 
Here’s another helpful link if you’re looking to implement this: https://www.digi.com/resources/documentation/Digidocs/90002258/#concepts/c_update_device_fw.htm Once on that page, click each of the links “Use a host processor to update the modem firmware…”. It’s worth skimming just for context. Note that this link pertains to the XBee 3 Cellular device, not the XBee 3 Zigbee, but the steps of invoking the bootloader and the XMODEM-CRC file transfer are similar.
 
It's also possible to reprogram the XBee’s bootloader. I believe the technique is similar (assert DTS and/or RTS, restart device, adjust baud rate, etc.). I haven’t done it by myself from scratch yet, but it’s important because some XBee firmware versions require first updating the bootloader.
 
Dig’s open source libraries  “xbee-ansic-library” (C code) and “xbee-python” (Python code for PC) both support updating XBee devices over serial. I’ve successfully done this myself with each of these libraries. These libraries also serve as a good reference if you’re trying to implement it yourself.
•	Relevant xbee-python docs: https://xbplib.readthedocs.io/en/latest/user_doc/update_the_xbee.html#updatefirmwarelocal
•	Relevant xbee-python sample code: https://github.com/digidotcom/xbee-python/blob/master/examples/firmware/LocalFirmwareUpdateSample/LocalFirmwareUpdateSample.py
•	Relevant header for the XBee C library: https://github.com/digidotcom/xbee_ansic_library/blob/master/include/xbee/firmware.h
•	I believe I followed this sample: https://github.com/digidotcom/xbee_ansic_library/blob/master/samples/posix/install_ebl.c
And here are some links I found helpful when re-implementing XMODEM-CRC myself:
•	XMODEM / YMODEM Protocol Reference by Chuck Forsberg (the 1988 version is an updated version of the 1985 original)
•	https://en.wikipedia.org/wiki/YMODEM - Links to the original protocol reference are at the bottom of this page.
•	https://gist.github.com/zonque/0ae2dc8cedbcdbd9b933 - I originally based this implementation upon this link.
•	https://github.com/digidotcom/xbee-python/blob/master/digi/xbee/util/xmodem.py - Implements both XMODEM and YMODEM.
•	https://github.com/digidotcom/xbee-python/blob/master/digi/xbee/firmware.py - This is what invokes xmodem.py above.
•	http://web.mit.edu/6.115/www/amulet/xmodem.htm - Good discussion of XMODEM-CRC.
•	https://pythonhosted.org/xmodem/xmodem.html - Contains good examples of XMODEM and XMODEM-CRC data flow!
 

## Dan's Tricks of the Trade


Documentation / Example Woes: Digi provides lots of Python example code (xbee-python library for Linux/Windows) as well as lots of MicroPython example code (xbee-micropython library). But all of these examples are just toy examples. There’s not a good reference design to show how to use it in an actual product. . I’ve always said that anyone can write a few hundred or thousand lines of code, but the real skill is in writing code that is tens of thousands of lines, and having all that code be testable and maintainable.

xbee-python: API is pretty good. But it has some quirks like polling much slower than callback approach. I wonder if there are other speed issues. Another drawback: Also, requires API Frames mode—it can’t put device into correct mode if it’s not already in that mode.

xbee-ansic-library: It could use some simple higher-level functions to make it easier to use.

PyCharm: It’s mostly great but has some problems. Annoying thing: It transfers all files in the directory, including files that you might not want to transfer! There’s no ignore pattern. That eats space on the device and makes things slower.

Times out when transferring files: Could be a bug in your MicroPython code, causes device to keep rebooting. Solution: ATPS0, reset, then MicroPython doesn’t start up.

Testing methodology:
    Recommendation: Develop in CPython with CPython versions of usocket, etc. And only doing an integration test in MicroPython.

    CPython implementations of usocket, etc. so that you can develop MicroPython with CPython.

    Rather than importing with ‘socket’, import with ‘usocket’. Simlarly for utime, umachine, etc. That way, the CPython and MicroPython versiosn won’t conflict. The only standard modules that don’t let us import them with the ‘u’ prefix are ‘micropython’ and ‘gc’. ‘micropython’ isn’t a problem because CPython doesn’t have one of those. But for ‘gc’, I made a ‘upython/ugc.py’ that wraps it. That way, all of your other ‘upython/*.py’ files can import ‘ugc’ instead of ‘gc’, which allows your code to be more platform-agnostic.

    I've tried running MicroPython unit tests, but the problem is that they end up eating up too much memory and storage on the device. You only have so much for your tests.

    Aside: I've tried running x86 build of MicroPython, but not much success-- limited networking library support.

What is the best way to ensure that all your MicroPython files on the XBee are up-to-date at bootup?

    Answer: Write some code on host microcontroller to read and validate the checksums.)

What is the best way to use the uos.bundle() feature?

    Answer: Avoid it at all costs. 1) there’s not a quick way to check contents of bundle—the hash it returns has some metadata so it’s not useful. So you’d have to end up storing your own hash in a field like ATKP or in a text file. 2) when you rebundle, it reboots micropython controller, so you have no way of knowing whether bundling succeeded or failed. 3) If something fails to compile or if micropython bundle runs out of space, you just end up with modules missing functions and classes. That’s NOT good. Your imports just fail silently. (this is an issue with micropython, but bundling adds another layer of complexity on this and make things worse.) 

If you MUST use it, I can give you some advice about hashing the files so that you can detect whether to rebundle or not. But you still have to watch out for the issues listed above, so beware.

What’s the best way to cross-compile .mpy files for the device?

Answer: Write a Python script and integrate it into your build pipeline.

main.py/main.mpy: We compile main.py to main.mpy and deploy the .mpy version to the device. Note that if the device already contains a main.py, it will run the main.py instead. It is therefore up to the host processor (if one) or else the MicroPython deployment process to ensure that no main.py file exists on the device. When I first started using XBees, I deployed .mpy versions of all files EXCEPT main.py so that you'd never have a case where you accidentally deploy an out-of-date main.py that keeps running at startup instead of your desired main.mpy file. But that approach has the following downsides: 1) waste RAM and time at startup because the device must compile the .py file every time, 2) more complexity because you need to train main.py as a special case, 3) you don't the compile-time checking advantages of cross-compiling main.py unless you compile it too. Short answer: Use main.mpy on the device.

delete_any_dot_py_files() in the micropython code – Though if possible, you want to be sure to delete main.py via commands in the the host microcontroller attached to the XBee before the micropython code even starts up.

Design your code in such a way that you can use xbee-python on PC or MicroPython on device. What I did for the network latency tests-- see main.py vs client.py. Here’s a more in-depth description: More recently, another technique I’ve used (but not shown in the attached sources) is re-implementing some of the calls like xbee.transmit() to use xbee-python under the hood. For example, in cpython/fakes/xbee.py, you can write a transmit() function with the same signature as xbee.transmit() on the real device. Inside your transmit(), you’d put the calls to the xbee-python library for Zigbee transmission. Then you connect an XBee to your PC and put it in API Frames mode. When you call invoke the transmit() function from your PC, xbee-python sends the correct API Frames over serial to the device, causing the device to send the Zigbee packets. This technique has the advantage that you can send real Zigbee packets to real devices (and get real responses if you re-implement receive()), rather than having to fake all the data. This technique still has the advantage of fast turn-around time--  no need to deploy MicroPython files to the device. You can get all the core logic of your app working this way, then when you’re happy with it, deploy the MicroPython files to the device for an integration test on the real hardware.

Logging from micropython over user data relay API frames. 

    Rationale: Want the MicroPython to be able to print log messages, but you’re using the device in API Frames mode so you can’t see the output of the REPL terminal. This is useful if you want to log the messages on the host microcontroller (via serial) or in your Mobile App (via BLE). 
    
    Another alternative: Pack log messages into XBee 3 Zigbee/802.15.4 packets. 
    
    Another alternative: open up a TCP socket connection to a logging service (if you’re using XBee 3 Cellular).
    
    Another option, for XBee 3 Cellular, is to use the secondary UART. See C:\Dan\Code\xbgw\README.md for more notes on that.

RUDR: Reliable User Data Relay Frames.
    Be sure you build a reliability protocol on top of user data relay frames. Because if you lose messages, you might get extremely confused and go down the wrong path. Enabling serial flow control is one way to make sure your host controller doesn’t get overwhelmed to the point that it can’t keep up and starts discarding stuff. But a reliability protocol with acks is definitely a safer way to go.

Catching exceptions at the top-level and logging them using the above logging approach.
    That way, if you have some error you didn’t account for, you make sure that you’ll be able to see it.

    Another option is logging unrecoverable failures to a file on the XBee’s filesystem for later inspection. Just take caution not to let the file grow too large and fill up the filesystem (e.g., if it gets caught in a loop of crashes, logging, and automatic restarts, it could fill up quite quickly if there aren’t limits) out to wear out the flash with too many write cycles.

    Be sure to check out my “exception_details()” MicroPython function, which gives you a stack trace about the exception that occurred.

Custom data in existing registers: Consider repurposing fields like ATKP (DRM Description), ATKC (DRM Contact), ATKL (DRM Location) to store whatever custom data you want if you don’t want to store it into the XBee 3’s filesystem.


XBEE 3 Cellular Thoughts:

    1.	They are very slow to download stuff—low bandwidth.
    2.	You really want to use flow control if transferring loads of data.
    3.	You really want reliability protocol on top of user data relay frames.
    4.	Note: My special AT&T VPN SIM can only access Remote Manager (dev, test, and prod environments); it does NOT seem to be able to access any other resources on the web.


Security concern: There’s only one password for BLE, so users can connect via their XBee Mobile App.


## PyCharm

- Concern: Plugin seems to time out when transferring lots of files.

- Note: They recently

- Note: There is a feature request for only transferring the files that have changed. Currently it deploys everything.

### PyCharm Setup Tips

- Set your PyCharm project root to be the top-level directory (i.e., `lps/micropython`
- In PyCharmm, right click the `lps/micropython/arch/micropython/app` directory and select `Mark Directory As`. .. `Sources Root`.
  This will allow it to find all the modules in this directory.
    - Reference: https://stackoverflow.com/questions/28326362/pycharm-and-pythonpath/57497936#57497936



## FAQ

- Q: Is there any reason to limit the number of MicroPython files / imported module?
  
  A: No. At one point I thought it made a difference, and that each module had an overhead
  of like a whopping 1kB, but my latest experiments show that this is not the case.
  
  So feel free to split your code across as many files as you want, within reason.


## Digi Industrial Gateway Bandwidth Conservation Notes

- TCP keepalive != DRM keepalive (EDP keepalive)
- Upstream and downstream keepalive. Specified in seconds. Crank them up to at least 15 minutes.
- Depends on the carrier. Different carriers have different drop-offs. Want to keep TCP connection alive
  so that you can have it actively communicate with DRM.
- Default is 1 minute. That will burn up over 10 MB per month.
- Write a Python program on GW to manage the window / duty cycle when DRM connection is active.
  e.g., only have DRM connection between specific range of hours.
- SM-SMS -- Tell gateway when to wake up and connect to DRM.
  - Generally use scheduled operations.
  - Make sure to have x disconnect when it's done.
- We can disable the TCP keepalive, as long as we have EDP keepalives frequently enough to keep the TCP connection open.
  - Note that the TCP keepalive setting in the gateway only applies to the DRM socket.
  - If you want to do any Python tcp sockets, your python code will have to set the TCP keepalive for those sockets.
    (Mike Wadsten says that in Linux, which is what the gateway is running, TCP sockets are set up with TCP keepalive off by default.)
- Note that you set two variables for EDP keepalives, one for each direction (uplink and downlink).
- https://www.digi.com/resources/documentation/digidocs/90001399-13/Default.htm#references/r-advanced-connectivity-settings.htm
- We'll definitely want to aggregate the data on the gateway before sending it up to remote manager,
  so that we can send it all up in a single batch. That way we can minimize TCP header overhead
  and TLS header overhead.


## Digi Remote Manager

- Examples / SCI / SM/UPD / RCI / Query Device State -- POST /ws/sci
- Examples / SCI / SM/UDP / RCI / Query Device Settings -- POST /ws/sci
- Examples / SCI / Data Service / Send Request -- This is how you can send messages to receive on the MicroPython side with digi.cloud

For the last example, see the code and comments in `xbf\archive\micropython\demo.py:digi_cloud_benchmark()` for details!


## XBee 3 Cellular Performance benchmarks

I switched SIM cards in my XBee 3 Cellular and I was able to complete the benchmarks! Results:

•	Issued HTTP request from MicroPython code. Average round-trip-time:
o	1.7 sec for http://api.ipify.org/
o	1.8 sec for http://www.micropython.org/ks/test.html
•	Issued HTTPS request from MicroPython code. Average round-trip-time:
o	2.0 sec for https://api.ipify.org/
o	2.2 sec for http://www.micropython.org/ks/test.html
•	Remote Manager: Issued requests using API Explorer. XBee 3 Cellular was configured for “stay connected to DRM” mode. Round-trip time:
o	Query Device State: Typically between 500 ms to 600 ms. Occasionally 1.5 sec. Worst case: 2.1 sec (cold start). (Note that Query Device State is handled by XBee firmware, not MicroPython code.)
o	Query Device Settings: Typically between 700 and 800 ms. Occasionally 1.4 sec. Worst case: 1.9 sec (cold start). (Note that Query Device Settings is handled by XBee firmware, not MicroPython code.)
o	MicroPython code (digi.cloud) module received Data Service requests issued by API Explorer and sent back response. RTT typically between 800 ms and 1 sec, though occasionally 2 seconds, and once as much as 6 seconds.

Note that I performed these experiments with an XBee 3 Cellular Cat-1 because I couldn’t get the SIM card on my XBee 3 LTE-M to work. However, based upon my own past experiences / qualitative observations from working with the two variants, I believe the latency is similar for small packets such as the ones in these tests.

I believe the main reason why the Remote Manager round-trip times were significantly faster than the HTTP/HTTPS requests was that the TCP+TLS connection to Remote Manager was already established, since the device was in “stay connected to DRM” mode. I believe if we maintain a TCP+TLS connection from MicroPython to some other server, such as an MQTT Broker, we’d see similar results. Of course, if you closed the MQTT connection between each MQTT request, you’d probably get similar performance to that of the HTTP requests. In other words, the overhead of establishing the connection likely accounts to for 1.0 to 1.5 seconds of the total round-trip time.

I’m not exactly sure what is causing this overhead to establish the connections. I don’t think the DNS lookup takes very long. Obviously there is more overhead for TLS connections to do all the handshaking (as evident from our HTTP / HTTPS numbers above). Perhaps it simply takes some time for the cell modem to open a TCP connection.

Sometime I’d like to do some more experiments with an XBee 3 Cellular LTE-M. And also with an MQTT broker (e.g., AWS). And also perhaps benchmark just the DNS lookup piece (using the AT LA command). But at least here’s some data to get you started.

Anyway,  to tie this back into your application with the XBee 3 Cellular in “always on” mode, I’d say that for a persistent TCP+TLS connection, we could expect a delay similar to that of Query Device State above. i.e., approximately 500 ms one way, or 1 sec round trip.


## Miscellaenous

- Does XCTU have a command-line version? YES! But only for local devices (doesn’t appear to be able to do remote deployment) https://www.digi.com/resources/documentation/digidocs/90001458-13/default.htm#task/t_command_line_load_profile.htm

- XBee 3 Cellular devices have 64kB of MicroPython heap RAM.  XBee 3 RF (802.15.4/Zigbee/DigiMesh) devices have 32kB of MicroPython heap RAM. They are unable to increase the XBee 3 RF heap RAM due to microprocessor hardware size constraints.

- Unescaped API Frames are preferred. Don't use Escaped API Frames unless you have a very good reason.


## Do NOT use XBee 3 Cellular as a TCP Listener

- This says it is possible: https://www.digi.com/resources/documentation/Digidocs/90002258/#reference/r_extended_socket_example_tcp.htm
  - But the Note on this page says it doesn't support TLS sockets.
  
- But we've had some customers having trouble with it. See XBCELL-6310.
