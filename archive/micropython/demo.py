def demo_blink_LED():
    ''' Demonstrates toggling a GPIO pin to drive an LED. '''
    
    from machine import Pin
    import time
    
    led = Pin("D5", Pin.OUT, value=0) # DIO5 = XBee3 Cellular "Associated Indicator" LED, which is Pin 15 of the through-hole package.
    
    for _ in range(10):
        time.sleep_ms(100)
        led.toggle()
    
    led.value(1)
    time.sleep_ms(2000)
    
    while True:
        time.sleep_ms(100)
        led.toggle()


def demo_sleep_mode():
    '''
    Demonstrates putting the XBee into sleep mode.
    This is NOT sleep in the creating-a-delay-in-the-time.sleep()-sense;
    it instead puts the XBee into low-power mode.
    Note that if ATSM != 0, you'll get an "EALREADY" OSError exception.
    https://www.digi.com/resources/documentation/digidocs/90002219/#reference/r_sleep_mp.htm
    '''
    from machine import Pin
    import time
    import xbee

    led = Pin("D5", Pin.OUT, value=0)
    xb = xbee.XBee()

    while True:

        # Blink at 5 Hz for 5 seconds.
        for _ in range(50):
            time.sleep_ms(100)
            led.toggle()

        # Start sleep mode.
        SLEEPTIME_ms=60000  # Sleep for 1 minute.
        xb.sleep_now(SLEEPTIME_ms, pin_wake=False)


def demo_prohibit_sleep():
    '''
    Prevent the XBee from going into sleep mode using the wake_lock
    Good for protecting critical sections of MicroPython code.
    https://www.digi.com/resources/documentation/digidocs/90002219/#reference/r_sleep_at_cmds.htm
    '''
    print("Starting prohibit sleep demo.")
    
    from machine import Pin
    import time
    import xbee
    
    led = Pin("D5", Pin.OUT, value=0)
    xb = xbee.XBee()

    with xb.wake_lock:  # Ensure that we cannot be interrupted with sleep in the middle of this.
        while True:
            time.sleep_ms(100)
            led.toggle()


def demo_soft_reboot():
    '''
    Demonstrates how to initiate a soft reboot from MicroPython.
    With a soft reboot, it just restarts the MicroPython interpreter
    (and restarts main.py/main.mpy (if configured to do so with the ATPS1 setting).
    It does not restart the entire device.
    https://www.digi.com/resources/documentation/digidocs/90002219/#tasks/t_reset_repl.htm
    Note that there does not appear to be a way to initiate a soft reset using AT commands,
    perhaps because a soft reset is specific to the MicroPython code.
    '''
    import machine
    machine.soft_reset()


def demo_hard_reboot():
    '''
    Demonstrates a hard boot of the entire XBee3 device using the ATFR command.
    https://www.digi.com/resources/documentation/digidocs/90002219/#tasks/t_reset_repl.htm)
    Note that this is the preferred mechanism to implement a hard reboot of the XBee3 device;
    there does not appear to be a MicroPython call that wraps this.
    '''
    import xbee
    xbee.atcmd('FR')


def demo_memory_usage():
    '''
    Demonstrates using the 'gc' module to print usage statistics and to invoke the garbage collector.
    Also demonstrates how the 'micropython' module can print some memory usage information.
    https://www.digi.com/resources/documentation/digidocs/90002219/#reference/r_module_gc.htm?
    '''
    import gc
    def stats():
        print("  gc.mem_free(): %s" % gc.mem_free())
        print("  gc.mem_alloc(): %s" % gc.mem_alloc())
        print("  total: %s" % (gc.mem_free()+gc.mem_alloc()))
    print("Before garbage collection:")
    stats()
    gc.collect()
    print("After garbage collection:")
    stats()
    
    print("Additional statistics:")
    import micropython
    micropython.mem_info()
    micropython.stack_use()


def demo_sms_message():
    '''
    Demonstrates sending an SMS message to your phone.
    Also demonstrates how to receive an SMS message.
    '''
    import network
    c = network.Cellular()
    c.sms_send("3332221111", "Hello from your XBee")
    # Now send a message back from your phone. Then call the following function to receive it:
    msg = c.sms_receive()
    print("Received: %s" % msg)


def power_test():
    '''
    Puts the XBee3 into sleep mode for a short amount of time, sends an HTTP request, then puts the device back to sleep.
    Then we can hook up some hardware instrumentation in order to measure both the quiescent power consumption (sleeping)
    as well as maximum power consumption (cellular transmitting).
    '''

    print("Launching power test.")
    
    from machine import Pin
    import network
    import time
    import urequests
    import xbee

    cell = network.Cellular()
    led = Pin("D5", Pin.OUT, value=0)
    xb = xbee.XBee()

    while True:

        # Put the XBee to sleep. Turn off the LED first to indicate that we're going to sleep.
        led.value(0)
        SLEEPTIME_ms=30000
        print("Going to sleep for %s seconds." % str(SLEEPTIME_ms/1000.0))
        xb.sleep_now(SLEEPTIME_ms, pin_wake=False)  # Execution blocks here for the specified time. Device goes into low power mode (NOT the same as time.sleep() which sleeps the thread!)

        # Now the device is awake.
        with xb.wake_lock:

            # Blink the LEDs for 2 seconds to indicate that we've woken up.
            print("Woke up!")
            for _ in range(20):
                led.toggle()
                time.sleep_ms(100)

            # Hold on the LED to indicate we're getting ready to transmit.
            led.value(1)
            time.sleep_ms(1000)
            
            # Attempt to establish cell connection.
            print("Checking for cell connection.")
            print("Is active (not airplane mode)? %s" % cell.active())
            for _ in range(600):
                print(".", end="")
                if cell.isconnected():
                    break
                time.sleep_ms(100)
            
            if not cell.isconnected():
                print("Unable to get cell connection.")
                for _ in range(8):
                    led.toggle()
                    time.sleep_ms(500)
                continue

            # Cell connection was successful!
            print("Got cell connection!")
            print(cell.ifconfig())
            print("SIM:", cell.config('iccid'))
            print("IMEI:", cell.config('imei'))
            print("Provider:", cell.config('operator'))
            print("Phone #:", cell.config('phone'))
            print("Cell signal strength: %s" % xbee.atcmd('DB'))

            # Transmit an HTTP request.
            try:
                r = urequests.get("http://api.ipify.org/")
                print("HTTP response: %s, %s" % (r.status_code, r.text))
            except Exception as ex:
                print("HTTP request failed. Exception: %s" % ex)


def demo_handle_api_frames():
    '''
    Provides loopback functionality. Receives a User Data Relay API frame
    from the serial interface, adds some data to it, then sends it back to the sender.
    
    How to run this demo:
    1) In XCTU's MicroPython Terminal, first put the XBee into MicroPython mode (+++-wait-ATAP4).
       Then press Ctrl+f, paste in the code, and compile it into /flash/main.mpy.
       Then press Ctrl+d to soft reboot and run the code.
       (Make sure there is no /flash/main.py file or that would get executed instead.)
       Alternatively, copy this code into /flash/main.py using XCTU's File System Manager tool
       (and then you can press the reset pushbutton to restart the system and run the new code).
       Then put the device back into API Mode with Escapes (+++-wait-ATAP2) so that it is ready to receive the data.
       Close the serial port in XCTU when done so that you can reopen the port with gecko.py.
    2) In another terminal, run api_frames_loopback_test() defined in gecko.py.
       That script will open the serial port using PySerial and send a User Data Relay message to MicroPython.
       The code below receives that message, appends to it, and then sends it back to the sender.

    Notes:
    - You could add the "+++-wait-ATAP4" commands here to streamline changing modes for testing.
    - You can also set up a loopback example within MicroPython. relay.send(relay.MICROPYTHON, b"blah") and then call relay.receive().
    '''

    print("Launching API frames demo.")

    from machine import Pin
    import time

    from xbee import relay

    led = Pin("D5", Pin.OUT, value=0) # DIO5 = XBee3 Cellular "Associated Indicator" LED, which is Pin 15 of the through-hole package.

    while True:
        rx = relay.receive()
        if rx is not None:
            dest = rx['sender']
            data = rx['message'] + b'world'
            relay.send(dest, data)
        time.sleep_ms(500)
        led.toggle()


def demo_dns_lookup():
    '''
    From this example in the Digi MicroPython Programming Guide: https://www.digi.com/resources/documentation/digidocs/90002219/#tasks/t_dns_lookup.htm
    '''
    import socket
    print("IP Address: %s" % socket.getaddrinfo('google.com', 80))


def demo_http_urequests():
    ''' Code to send an HTTP request.'''
    import urequests
    r = urequests.get("http://api.ipify.org/")
    r.status_code
    r.text
    r.content

# http_benchmark sends requests to a given URL and reports on the amount of time required to hear the response.
# Note that this also supports https URLs as well. Usage examples:
# http_benchmark("http://api.ipify.org/", 10)
# http_benchmark("https://api.ipify.org/", 10)
# http_benchmark("http://www.micropython.org/ks/test.html", 10)
# http_benchmark("https://www.micropython.org/ks/test.html", 10)
def http_benchmark(url: str, num_samples: int) -> None:
    if num_samples < 1:
        print("Error, must collect at least one data sample!")
        return
    import urequests
    import utime
    data = []
    for _ in range(num_samples):
        print("Sending request to %s..." % url)
        before = utime.ticks_ms()
        r = urequests.get(url)
        after = utime.ticks_ms()
        delta = utime.ticks_diff(after, before)
        data.append(delta)
        print("status_code=%s, content=%s, time=%s ms" % (r.status_code, r.content, delta))

    # Calculate stats:
    data.sort()
    outliers = []
    if len(data) > 2:
        outliers = [data[0], data[-1]]
        data = data[1:len(data)-1]  # Throw out 2 outliers.
    middle = len(data) // 2
    odd_num = len(data) % 2 == 0
    median = sum(data[middle-1:middle+1])/2.0 if odd_num else data[middle]
    mean = sum(data) / len(data)

    print("Outliers: %s" % outliers)
    print("Results (after eliminating outliers):")
    print("  Data: %s" % data)
    print("  Length: %s" % len(data))
    print("  Median: %s" % median)
    print("  Mean: %s" % mean)
    print("  Min: %s" % min(data))
    print("  Max: %s" % max(data))


# digi_cloud_benchmark waits for requests from Digi Remote Manager,
# then immediately sends a response upon receiving it. That way,
# you can benchmark the RTT from the request initiator side (DRM REST API).
# See `Examples / SCI / Data Service / Send Request` in the DRM API Explorer.
# https://www.digi.com/resources/documentation/Digidocs/90001437-13/default.htm#reference/r_sci_available_operators.htm
# https://github.com/digidotcom/xbee-micropython/tree/master/samples/remote_manager/read_device_request
# Be sure you set `target_name="micropython"` in the `<device_request>` tag as shown in the above xbee-micropython sample!
def digi_cloud_benchmark() -> None:
    from digi import cloud
    while True:
        try:
            request = cloud.device_request_receive()
            if request is not None:
                data = request.read()
                request.write(bytes('ack', "utf-8"))
                request.close()
                decoded_data = data.decode("utf-8").strip()
                print("GOT DATA: %s" % decoded_data)
        except Exception as ex:
            print("ERROR: %s" % ex)


def demo_http_get():
    '''
    From the example in the DigiMicroPython Programming Guide: https://www.digi.com/resources/documentation/digidocs/90002219/#tasks/t_send_http_req.htm

    Note that this is actually CPython code intended to be run on a laptop, NOT MicroPython code!!!
    '''
    import socket

    def http_get(url):
        scheme, _, host, path = url.split('/', 3)
        s = socket.socket()
        try:
            s.connect((host, 80))
            request=bytes('GET /%s HTTP/1.1\r\nHost: %s\r\n\r\n' % (path, host), 'utf8')     
            print("Requesting /%s from host %s\n" % (path, host))
            s.send(request)
            while True:
                print(str(s.recv(500), 'utf8'), end = '') 
        finally:
            s.close()
    
    http_get('http://www.micropython.org/ks/test.html')


def demo_https():
    '''
    Demonstrates a simple HTTPS request using MicroPython's ussl module to wrap the TCP socket.

    References:
    - See the MicroPython ussl module docs in the Digi MicroPython Prgoramming Guide: https://www.digi.com/resources/documentation/digidocs/90002219/#reference/r_ussl.htm
    - See the HTTPS example in the Digi GitHub xbee-micropython repo: https://github.com/digidotcom/xbee-micropython/blob/master/samples/cellular/aws/aws_https/main.py
    - Here's the README accompanying the above link: https://github.com/digidotcom/xbee-micropython/blob/master/samples/cellular/aws/aws_https/README.md
    - And the above README references this README: https://github.com/digidotcom/xbee-micropython/blob/master/samples/cellular/aws/README.md   
    - Apparently Base64 PEM files are the correct type of certificate, according to this: https://www.digi.com/resources/documentation/digidocs/90002219/#reference/r_syntax_ussl.htm
    '''
    print("HTTPS test!")

    import network
    import time
    import usocket
    import ussl

    HOSTNAME = "a346ga75b9eiwl-ats.iot.us-west-2.amazonaws.com"
    #HOSTNAME = "api.ipify.org"  # Needs sectigo.cer
    PORT = 8443
    #PORT = 443
    
    THING_NAME = b'CS-XBee'

    CA_CERTS="/flash/cert/fromdevice-aws.ca"
    #CA_CERTS="/flash/cert/aws.ca"
    #CA_CERTS="/flash/cert/ipify.cer"

    s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM, usocket.IPPROTO_SEC)
    w = ussl.wrap_socket(s,
                        ca_certs=CA_CERTS,
                        certfile='/flash/cert/aws.crt',
                        keyfile='/flash/cert/aws.key')
    w.settimeout(1)

    print("Attempting to connect...", end="")
    w.connect( (HOSTNAME, PORT) )
    print(" Connected to AWS.")

    tx = b'GET /things/%s/shadow HTTP/1.0\r\nHost: %s\r\n\r\n' % (THING_NAME, HOSTNAME)
    #tx = b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nUser-Agent: curl/7.64.0\r\nAccept: */*\r\n\r\n"

    w.write(tx)
    print("TX: %s" % tx)

    rx = str( w.read(1024), 'utf-8' )
    print("RX %s" % rx)

    w.shutdown(usocket.SHUT_RDWR)
    w.close()


def demo_test_aws_connection():
    '''
    From https://www.digi.com/resources/documentation/digidocs/90002219/default.htm#tasks/t_test_connection.htm
    '''

    # There's an issue in which the XBee3CellularLTE-CAT1 does not support AWS endpoints that end in "-ats".
    # See https://jira.digi.com/browse/XBCELL-4760 for details. I confirmed this issue on 2019-06-18.
    # The workaround is that you must remove the "-ats" part of the AWS endpoint string 'ak87jc7d58d2m-ats.iot.us-east-2.amazonaws.com'
    # so that it uses a legacy authentication server.
    # The XBee3CellularLTE-CATM/NB-IoT does not have this issue; you should use the "-ats" AWS endpoint with the CATM device.
    # In fact, the CATM device doesn't work with legacy endpoints that do not contain "-ats"!
    # Note that you use the same version of the root CA file (aws.ca) for both endpoints.
    # (Note that the aws.ca that I've been using is the one signed by "Starfield Technologies, Inc.".)
    #
    # In summary:
    # - For the XBee3CellularLTE-CATM/NB-IoT, you must use:  b'ak87jc7d58d2m-ats.iot.us-east-2.amazonaws.com'
    # - For the XBee3CellularLTE-CAT1, you mustuse:  b'ak87jc7d58d2m.iot.us-east-2.amazonaws.com'
    #
    # For more information about Amazon Trust Services (ATS), see:
    # - https://docs.aws.amazon.com/general/latest/gr/rande.html
    # - https://www.amazontrust.com/repository/
    # - https://aws.amazon.com/blogs/security/how-to-prepare-for-aws-move-to-its-own-certificate-authority/

    aws_endpoint = b'ak87jc7d58d2m-ats.iot.us-east-2.amazonaws.com'
    #aws_endpoint = b'ak87jc7d58d2m.iot.us-east-2.amazonaws.com'
    thing_type = b'XBee3Cellular'
    thing_name = b'DanXBee'
    
    print("Using endpoint: %s" % aws_endpoint)

    import usocket, ussl

    s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM, usocket.IPPROTO_SEC)
    s.setblocking(False)
    w = ussl.wrap_socket(s,
        keyfile='/flash/cert/aws.key',
        certfile='/flash/cert/aws.crt',
        ca_certs='/flash/cert/aws.ca')

    w.connect( (aws_endpoint, 8443) )
    w.write(b'GET /things/%s/shadow HTTP/1.0\r\nHost: %s\r\n\r\n' % (thing_name, aws_endpoint))
    
    while True:
        data = w.read(1024)
        if data:
            print(str(data, 'utf-8'))
            break
    w.close()


def demo_test_ipify():
    '''
    From https://www.digi.com/resources/documentation/digidocs/90002219/default.htm#tasks/t_test_connection.htm
    '''
    
    print("Running demo_test_ipify()...")

    import usocket, ussl

    s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM, usocket.IPPROTO_SEC)
    s.setblocking(False)
    w = ussl.wrap_socket(s,
        keyfile='/flash/cert/aws.key',
        certfile='/flash/cert/aws.crt',
        ca_certs='/flash/cert/sectigo.cer')

    w.connect( (b'api.ipify.org', 443) )
    w.write(b'GET / HTTP/1.1\r\nHost: api.ipify.org\r\nUser-Agent: curl/7.64.0\r\nAccept: */*\r\n\r\n')

    while True:
        data = w.read(1024)
        if data:
            print(str(data, 'utf-8'))
            break
    w.close()



def main():
    #power_test()
    demo_handle_api_frames()


if __name__ == "__main__":
    main()
