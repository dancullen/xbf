from common import to_hex, APIFrame, ATCommand, TXRequest, UserDataRelay

import argparse
import binascii
import serial
import time
import unittest


def parse_arguments():
    parser = argparse.ArgumentParser(description="This script runs unit tests and integration tests.")
    parser.add_argument('--integration', required=False, action="store_true", default=False,
                        help="Run the integration tests instead of the unit tests.")
    args = parser.parse_args()
    return args


class TestAPIFrame(unittest.TestCase):
    
    def test_checksums(self):

        # Uses example from the section ["Calculate and verify checksums" from the XBee Cellular User Guide](https://www.digi.com/resources/documentation/Digidocs/90002258/#Tasks/t_calculate_checksum.htm).
        MSG_ENTIRE = binascii.unhexlify("7E000A010150010048656C6C6FB8")
        MSG_DATA = binascii.unhexlify("010150010048656C6C6F")
        MSG_START_CHAR = b'\x7E'
        MSG_LENGTH = b'\x00\x0A'
        MSG_CHECKSUM = b'\xB8'

        # Test checksum calculation.
        self.assertEqual(MSG_CHECKSUM, APIFrame.calculate_checksum(MSG_DATA))

        # Test checksum verification.
        self.assertTrue( APIFrame.verify_checksum(MSG_ENTIRE[3:]) )                             # Must first strip start character and length bytes.
        self.assertFalse( APIFrame.verify_checksum(MSG_ENTIRE[3:].replace(b"\xB8", b"\xB9")) )  # Modify checksum. It should not pass now.

    def test_escaping(self):

        # Use example from the section ["Example: escape an API frame" from the XBee Cellular User Guide](https://www.digi.com/resources/documentation/Digidocs/90002258/#Reference/r_example_escape_frame.htm).
        MSG_TO_BE_ESCAPED = binascii.unhexlify("000F17010013A20040AD142EFFFE024E496D")  # Note that we've omitted the start character (0x7E) from the start of this message because everything needs to be escaped EXCEPT for the start character.
        MSG_ESCAPED = binascii.unhexlify("000F1701007D33A20040AD142EFFFE024E496D")      # Notice that the 0x13 has been escaped as 0x7D 0x33.

        self.assertEqual( MSG_ESCAPED, APIFrame.escape(MSG_TO_BE_ESCAPED) )


class TestUserDataRelay(unittest.TestCase):

    def test_packing(self):

        UDR_ENTIRE = binascii.unhexlify("7e00082d000268656c6c6fbc")
        self.assertEqual( UDR_ENTIRE, UserDataRelay(b'hello').packed )


class TestPythonXBeeLibrary:
    def test_cellular_functionality():
        print("Experimenting with python-xbee library - cellular functions")

        from digi.xbee.devices import CellularDevice
        from digi.xbee.models.protocol import IPProtocol
        from ipaddress import IPv4Address

        device = CellularDevice("COM7", 115200)
        #import pdb; pdb.set_trace()

        device.open()
        device.send_ip_data(IPv4Address("52.43.121.77"), 11001, IPProtocol.TCP, "Hello XBee World!") # Send a message to Digi's echo server.
        ip_message = device.read_ip_data()
        print(ip_message.data.decode("utf8") if ip_message is not None else "ERROR")
        
        xbee_message = device.read_data()
        remote_device = xbee_message.remote_device
        data = xbee_message.data
        is_broadcast = xbee_message_is_broadcast
        timestamp = xbee_message.timestamp

        device.close()


    @staticmethod
    def test_get_parameter():
        print("Experimenting with python-xbee library - query parameters")

        from digi.xbee.devices import CellularDevice, XBeeDevice
        
        # Enable logging in the python-xbee library.
        import logging, digi.xbee.devices, digi.xbee.reader
        logging.getLogger(digi.xbee.devices.__name__).setLevel(logging.DEBUG)
        logging.getLogger(digi.xbee.reader.__name__).setLevel(logging.DEBUG)

        xb = CellularDevice("COM7", 115200)  # Alternatively: XBeeDevice("COM7", 115200)
        xb.open()

        p = xb.get_parameter("AP")
        print("GOT: %s" % p)
        xb.close()


    @staticmethod
    def test_xbee_filesystem_commands():
        print("Need to reverse-engineer syntax of the API Frames command with an AT Command that takes a parameter that is longer than a single byte.")

        from digi.xbee.devices import CellularDevice

        import logging, digi.xbee.devices, digi.xbee.reader
        logging.getLogger(digi.xbee.devices.__name__).setLevel(logging.DEBUG)

        xb = CellularDevice("COM7", 115200)
        xb.open()

        try:
            # I scoured the [xbee-python library docs](https://xbplib.readthedocs.io/en/latest/index.html)
            # to see if they have any support for the ATFS (file system) commands, but I couldn't find anything.
            # The closest I could find were these:
            #   p = xb.execute_command("FS HASH /flash/missing.txt")    # DOESN'T WORK
            #   p = xb.set_parameter("FS", b"HASH /flash/missing.txt")  # DOESN'T WORK
            # But they didn't work.
            #
            # Aha! Just found the following notes in the [XBee3 Cellular User Guide](https://www.digi.com/resources/documentation/Digidocs/90002258/#Containers/cont_at_cmd_file_system.htm): 
            #  "To access the file system, Enter Command mode and use the following commands.
            #   All commands block the AT command processor until completed and only work from Command mode;
            #   they are not valid for API mode or MicroPython's xbee.atcmd() method."
            #
            # So that answers my question.
            #
            # So this experiment has changed my perspective a little bit. I'm now thinking
            # that we should use AT Command Mode to do a bunch of the configuration,
            # rather than the AT Command API Frame message. Good to know!
            #
            # For more information on the xbee.atcmd() MicroPython function: https://www.digi.com/resources/documentation/digidocs/90002219/#reference/r_function_atcmd.htm
            pass
        except Exception as ex:
            print("GOT: %s" % ex)
        #import pdb; pdb.set_trace()
        xb.close()


    @staticmethod
    def test_aws_connection():
        '''
        Based on https://github.com/digidotcom/python-xbee/blob/master/examples/communication/ip/ConnectToEchoServerSample/ConnectToEchoServerSample.py
        which is documented on https://xbplib.readthedocs.io/en/latest/user_doc/communicating_with_xbee_devices.html
        '''

        print("Running TestPythonXBeeLibrary.test_aws_connection()...")

        # @todo enable logging

        from ipaddress import IPv4Address
        from digi.xbee.devices import CellularDevice
        from digi.xbee.models.protocol import IPProtocol

        xb = CellularDevice("COM7", 115200)

        try:
            xb.open()

            #####################

            #DEST_ADDR = "52.43.121.77"
            #DEST_PORT = 11001
            #PROTOCOL = IPProtocol.TCP
            #tx = "Hello XBee!"

            #####################

            aws_endpoint = b'ak87jc7d58d2m.iot.us-east-2.amazonaws.com'
            #aws_endpoint = b'ak87jc7d58d2m-ats.iot.us-east-2.amazonaws.com'
            thing_type = b'XBee3Cellular'
            thing_name = b'DanXBee'

            DEST_ADDR = "18.217.238.169"  # @todo Implement DNS lookup for the aws endpoint! For now I've just hard-coded DEST_ADDR.
            DEST_PORT = 8443
            PROTOCOL = IPProtocol.TCP_SSL

            tx = b"GET /things/%s/shadow HTTP/1.0\r\nHost: %s\r\n\r\n" % (thing_name, aws_endpoint)

            # Set up TLS v1.2 and paths to certs.
            xb.set_parameter("TL", b"\x03")
            xb.set_parameter("$0", b"/flash/cert/aws.ca;/flash/cert/aws.crt;/flash/cert/aws.key")
            print("TL: %s" % xb.get_parameter("TL"))
            print("$0: %s" % xb.get_parameter("$0"))

            # The TLS requests might take a little longer than the default so increase timeout.
            print("Old timeout: %s" % xb.get_sync_ops_timeout())
            xb.set_sync_ops_timeout(10)
            print("New timeout: %s" % xb.get_sync_ops_timeout())

            #####################

            xb.send_ip_data( IPv4Address(DEST_ADDR), DEST_PORT, PROTOCOL, tx )
            print("TX: %s" % tx)

            rx = xb.read_ip_data()
            if rx is None:
                print("Echo response was not received from the server.")
            else:
                print("RX: %s" % rx.data.decode("utf8"))

        except RuntimeError as ex: #Exception as ex:
            print("Got exception! %s" % ex)

        finally:
            print("Cleaning up.")
            if xb is not None and xb.is_open():
                xb.close()


    @staticmethod
    def test_tcp():
        '''
        Test sending a simple TCP message using the xbee-python library.
        '''
        print("Running TestPythonXBeeLibrary.test_tcp()...")


        print("Running TestPythonXBeeLibrary.test_aws_connection()...")

        # @todo enable logging

        from ipaddress import IPv4Address
        from digi.xbee.devices import CellularDevice
        from digi.xbee.models.protocol import IPProtocol

        xb = CellularDevice("COM7", 115200)

        xb.open()
        
        DEST_ADDR = "107.22.215.20"  # @todo implement DNS lookup for the aws endpoint! For now I've just hard-coded it.
        DEST_PORT = 80
        PROTOCOL = IPProtocol.TCP

        tx = b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nUser-Agent: curl/7.64.0\r\nAccept: */*\r\n\r\n"
            
        # The TCP request might take a little longer than the default so increase timeout.
        print("Old timeout: %s" % xb.get_sync_ops_timeout())
        xb.set_sync_ops_timeout(10)
        print("New timeout: %s" % xb.get_sync_ops_timeout())

        # Send the data.
        xb.send_ip_data( IPv4Address(DEST_ADDR), DEST_PORT, PROTOCOL, tx )
        print("TX: %s" % tx)

        # Receive response.
        rx = xb.read_ip_data()
        if rx is None:
            print("Response was not received from the server.")
        else:
            print("RX: %s" % rx.data.decode("utf8"))
                
        xb.close()


class IntegrationTests:

    @staticmethod
    def test_api_user_data_relay():
        '''
        Transmit API frame message over the serial interface and receive the response.
        '''
        print("Launching API user data relay test.")

        ser = serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
        tx = UserDataRelay(b'hello')
        ser.write(tx.packed)
        print("TX: %s" % tx)

        time.sleep(0.5)
        rx = ser.read(100)
        print("RX: %s" % rx)

        ser.close()

    def test_api_AT_Command():
        print("Launching API AT Command test.")
        ser = serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
        tx = ATCommand(b"AP", b"")
        ser.write(tx.packed)
        print("TX: %s" % tx)

        time.sleep(1)
        rx = ser.read(100)
        print("RX: ATResponse(bytes=%s, hex=%s)" % (rx, to_hex(rx)) )

        ser.close()

    @staticmethod
    def test_sockets_tcp():
        '''
        This isn't actually an XBee test, but rather just a simple Python sockets test.
        Just so that we know we're formatting the HTTP payload correctly.
        https://stackoverflow.com/questions/5755507/creating-a-raw-http-request-with-sockets
        '''
        print("TCP sockets test.")
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dst = ("api.ipify.org", 80)  # ("107.22.215.20", 80)
        s.settimeout(1)  # Use blocking sockets with a timeout of N seconds.
        s.connect(dst)
        s.sendall(b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nUser-Agent: curl/7.64.0\r\nAccept: */*\r\n\r\n")
        response = b""
        try:
            while True:
                print("Receiving...", end='')
                tmp = s.recv(1024) # If you use blocking sockets, this could hang for up to N seconds (see settimeout(N)) if the web server doesn't call shutdown() on their end. Which is often the case.
                if not tmp:  # If recv() EVER returns zero bytes, the socket is closed. https://docs.python.org/3/howto/sockets.html
                    break;
                print("Got %s bytes!" % len(tmp))
                response += tmp
        except Exception as ex:
            print("Exception: %s" % ex)
        print("Response: %s" % response)
        s.shutdown(socket.SHUT_RDWR)
        s.close()

    def test_sockets_tls():
        '''
        Like test_sockest_tcp(), this function is meant to be run on your PC using a standard Python3 CPython interpreter.
        But instead of using TCP sockets for the HTTP request, it instead uses a TLS socket to perform the HTTP request--
        i.e., it does a simple HTTPS request. The point of this is to make sure we can connect to the server properly
        using these certs. We could instead have used 'curl' or 's_client' to do this testing, but the nice thing about
        doing this with Python is that it is a little more transparent as to what is going on.
        '''
        print("TLS sockets test.")
        import socket, ssl
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Note that all three certificate files below succeed if ssl.wrap_socket(cert_reqs=None), which is the default beahvior.
        # However, if you set cert_reqs=ssl.CERT_REQUIRED, we get some errors:
        # - aws.ca: "ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain (_ssl.c:1056)
        # - letsencrypt.ca: ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain (_ssl.c:1056)
        # - comodo.cer: ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get issuer certificate (_ssl.c:1056)
        # And if you use sectigo.ca, it works, no errors!
        #CAFILE = '../cert/aws.ca'
        #CAFILE = '../cert/letsencrypt.ca'
        #CAFILE = '../cert/api.ipify.org/comodo.cer'
        CAFILE = '../cert/api.ipify.org/sectigo.cer'
        w = ssl.wrap_socket(s,
                            ca_certs=CAFILE,
                            certfile='../cert/aws.crt',
                            keyfile='../cert/aws.key',
                            cert_reqs=ssl.CERT_REQUIRED)
        w.settimeout(1)
        w.connect( ("api.ipify.org", 443) )
        w.write(b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nUser-Agent: curl/7.64.0\r\nAccept: */*\r\n\r\n")
        response = w.read(1024)
        print("Response: %s" % response)
        w.shutdown(socket.SHUT_RDWR)
        w.close()


    @staticmethod
    def test_aws_connection():
        '''
        From https://www.digi.com/resources/documentation/digidocs/90002219/default.htm#tasks/t_test_connection.htm
        '''
        aws_endpoint = b'ak87jc7d58d2m-ats.iot.us-east-2.amazonaws.com'
        thing_type = b'XBee3Cellular'
        thing_name = b'DanXBee'

        import socket, ssl

        s = socket.socket()
        w = ssl.wrap_socket(s,
            keyfile='../cert/aws-dan/aws.key',
            certfile='../cert/aws-dan/aws.crt',
            ca_certs='../cert/aws-dan/aws.ca')
        w.connect((aws_endpoint, 8443))
        #w.connect(("18.217.238.169", 8443))  # Can also connect using the IP address returned from the DNS lookup.
        #w.connect(("18.221.142.15", 8443))   # Looks like the AWS load balancer has assigned more than one IP address. Each of these works.
        tx = b'GET /things/%s/shadow HTTP/1.0\r\nHost: %s\r\n\r\n' % (thing_name, aws_endpoint)
        w.write(tx)
        print("TX: %s" % tx)
        rx = str(w.read(1024), 'utf-8')
        print("RX: %s" % rx) 
        w.close()


    @staticmethod
    def test_dns_lookup_on_xbee():
        '''
        Demonstrates DNS lookup.

        First of all, can we perform this in API Frames Mode, or do we need to do it in AT Command mode?
        According to the section [LA (Lookup IP Address of FQDN)](https://www.digi.com/resources/documentation/Digidocs/90002258/#Reference/r_cmd_LA.htm) in the XBee User Guide,
        it states, "When you issue LA in API mode, the IP address is formatted in binary four byte big-endian numeric value. In all other cases (for example, Command mode)
        the format is dotted decimal notation."
        So this seems to imply that it is possible in AT command mode.
        Let's put it to the test.

        Example:
        - AT Command Mode: b'ATLA google.com\r" returns b"172.217.8.14'
        - API Frames Mode: b'~\x00\t\x88\tLA\x00\xac\xd9\x01\xce\x8d'

        So it works! Yay! So we can indeed perform DNS lookup using API Frames Mode!
        '''

        with serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1) as ser:
            tx = ATCommand(b"LA", b"google.com").packed
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("Got: %s" % rx)

        #print("Launching API tcp frames test.")


    @staticmethod
    def test_api_tcp():
        '''
        Test transmitting TCP messages using API frames.
        '''
        print("Launching API tcp frames test.")
        ser = serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
        tx = TXRequest(payload=b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nUser-Agent: curl/7.64.0\r\nAccept: */*\r\n\r\n", dst="23.21.121.219")

        ser.write(tx.packed)
        print("TX: %s" % tx)

        for i in range(5):
            time.sleep(1)
            rx = ser.read(1024)
            print("RX: NotYetParsed(bytes=%s, hex=%s)" % (rx, to_hex(rx)) )

        ser.close()

    @staticmethod
    def test_api_tls():
        '''
        Test transmitting TCP messages with SSL/TLS using API frames.
        Note that this also contains the commands to set up the TLS profiles.

        Note that if you have a typo in the certs filename, you'll get this: "hex=7E 00 03 89 01 86 EF" where the 0x86 means "Invalid TLS configuration (missing file, etc.)".

        If you try to connect to a server that doesn't exist, you'll get "hex=7E 00 03 89 01 82 F3" is a "TX Status" message and the 0x82 means "No Server".

        If you try to connect to the wrong port / invalid port on a server that exists, you'll get "hex=7E 00 03 89 01 80 F5" where the 0x89 is the "TX Status" message type and the 0x80 means "Connection Refused" .

        For more details on the codes returned by the "TX Status" API Frame message, see: https://www.digi.com/resources/documentation/Digidocs/90002258/#Reference/r_frame_0x89_cell.htm)
        '''
        print("Launching the API frames SSL/TLS test.")

        ser = serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

        print("Using the following XBee TLS Profile 0 configuration:")
        tx = ATCommand(b"$0", b"").packed  # @todo what string needs to go in here to set up TLS???
        ser.write(tx)
        print("TX: %s" % tx)
        rx = ser.read(1024)
        print("RX: %s" % rx)

        print("Now performing the HTTPS request.")
        tx = TXRequest(payload=b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nUser-Agent: curl/7.64.0\r\nAccept: */*\r\n\r\n", dst="23.23.243.154", tls_profile=b'\x00')
        ser.write(tx.packed)
        print("TX: %s" % tx)

        for i in range(5):
            time.sleep(1)
            rx = ser.read(1024)
            print("RX: NotYetParsed(bytes=%s, hex=%s)" % (rx, to_hex(rx)) )

        ser.close()

    @staticmethod
    def test_api_aws_connection():
        '''
        Test transmitting SSL/TLS-secured TCP messages to AWS using API frames.
        
        Assumes XBee operating mode is API Frames With Escapes (ATAP2).
        '''

        print("Launching the AWS API frames test.")

        with serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1) as ser:

            DO_CONFIG = False
            DO_DNS_LOOKUP = True

            aws_endpoint = b'ak87jc7d58d2m.iot.us-east-2.amazonaws.com'
            #aws_endpoint = b'ak87jc7d58d2m-ats.iot.us-east-2.amazonaws.com'
            thing_type = b'XBee3Cellular'
            thing_name = b'DanXBee'

            if DO_CONFIG:
                print("Configuring the XBee TLS settings.")

                # Set IP protocol to SSL over TCP communication.
                # UPDATE: I believe this setting applies only to Transparent Mode, but we'll set it just in case.
                tx = ATCommand(b"IP", b"\x04").packed
                ser.write(tx)
                print("TX: %s" % tx)
                rx = ser.read(1024)
                print("RX: %s" % rx)

                # Set up TLS v1.2.
                tx = ATCommand(b"TL", b"\x03").packed
                ser.write(tx)
                print("TX: %s" % tx)
                rx = ser.read(1024)
                print("RX: %s" % rx)

                # Set up paths to certs.
                tx = ATCommand(b"$0", b"/flash/cert/aws.ca;/flash/cert/aws.crt;/flash/cert/aws.key").packed  # Set up paths to certs
                ser.write(tx)
                print("TX: %s" % tx)
                rx = ser.read(1024)
                print("RX: %s" % rx)

            else:
                print("Skipping config.")

            if DO_DNS_LOOKUP:
                print("Now performing the DNS lookup.")

                tx = ATCommand(b"LA", aws_endpoint).packed
                ser.write(tx)
                print("TX: %s" % tx)
                rx = ser.read(1024)
                print("Got: %s" % rx)
                if len(rx) < 13:
                    raise Exception("DNS lookup failed.")
                ip_addr = ".".join(["%i" % i for i in rx[8:12]])  # This converts something like b"~\x00\t\x88\tLA\x00\x12\xd9\xee\xa9_" to something like "18.221.142.15"
                print("Got: %s" % ip_addr)

            else:
                print("Skipping DNS lookup; using hard-coded IP address.")
                ip_addr = "18.224.102.166"

            print("Now performing the HTTPS request.")

            payload = b"GET /things/%s/shadow HTTP/1.0\r\nHost: %s\r\n\r\n" % (thing_name, aws_endpoint)
            tx = TXRequest(payload=payload, dst=ip_addr, tls_profile=b'\x00', tls_port=8443)
            ser.write(tx.packed)
            print("TX: %s" % tx)

            for i in range(10):
                time.sleep(1)
                rx = ser.read(1024)
                print("RX: NotYetParsed(bytes=%s, hex=%s)" % (rx, to_hex(rx)) )


    @staticmethod
    def test_detect_and_set_mode():
        '''
        First attempt to put the XBee into AT Mode so that we can put it into API Mode With Escapes (ATAP2).
        Then all subsequent commands will be API Frames commands, many of which will be the AT Command API Frames message,
        since it is a convenient way to perform AT Commands.
        
        Note that this code will try several times to put the XBee into AT Mode,
        trying several different baud rates if necessary, in order to determine the correct mode.
        
        This code next queries the following information from the XBee:
        - ATAP (Xbee operating mode)
        - ATBD (serial baud rate)
        - ATVR (firmware version)
        - ATVL (verbose firmware version)
        - ATHV (hardware version)
        - ATFS HASH /flash/main.mpy (get SHA256 checksum of the micropython source file to verify that it has the correct file)
        - ATPS (python autostart)
        - ATCK (configuration CRC) (A quick way to detect an unexpected configuration change of the device.)

        If anything is not set as we would expect, this code then sets those options.
        For example, it sets the above settings and also deploys the micropython code.

        To summarize, this test performs all the steps that the Connect Sensor's EFM32 Gecko microcontroller
        will need to do in order to configure the device and check its settings.
        
        @todo Be sure to check SHA256sum of /flash/main.mpy on the device using AT commands.
        '''
        
        # Note that we use a context manager ("with" statement) here so that it handles calling Serial.close() for us.
        
        with serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1) as ser:

            # Attempt to enter AT Command Mode.

            BAUD_RATES_TO_TRY = [115200, 9600, 38400, 19200, 57600, 230400, 4800, 2400, 1200]  # Sorted in order of likelihood that the device will be in that baud rate.
            NUM_RETRIES_AT_EACH_BAUD = 2

            success = False

            for bd in BAUD_RATES_TO_TRY:

                print("Baud: %s" % bd)

                for _ in range(NUM_RETRIES_AT_EACH_BAUD):

                    ser.baudrate = bd

                    tx=b"+++"
                    ser.write(tx)
                    print("TX: %s" % tx)
                    time.sleep(1.25)  # Whitespace.

                    rx = ser.read(1024)
                    print("RX: %s" % rx)

                    if rx == b'OK\r':
                        success = True
                        break

                if success:
                    break

            if not success:
                raise Exception("Unable to enter AT command mode.")

            # Check and set up files in the XBee's filesystem.
            # Since we'll need to use the ATFS command, and the ATFS command cannot be used within API mode (e.g., as explained on [this page](https://www.digi.com/resources/documentation/Digidocs/90002258/#Containers/cont_at_cmd_file_system.htm)),
            # we'll perform this configuration in AT Command Mode, NOT by using API Mode's AT Command message.
            print("@todo transfer the certificates files and/or check their sha256 hashes")
            print("@todo also check sha256 hash of /flash/main.mpy")

            # Configure SSL/TLS Profiles, which is how you set up the certificates to use.
            # For the SSL/TLS-related AT Commands, see the ["TLS AT commands"](https://www.digi.com/resources/documentation/Digidocs/90002258/#Reference/r_tls_at_cmds.htm) section of the user guide.
            # Note that although "AT$0" command works with the API Frames AT Command message (unlike the ATFS commands),
            # we might as well just use AT Command Mode here to set it up because we'll have to use AT Command Mode
            # to do the file transfer and hash check (using ATFS commands).
            tx = b"ATTL\r"
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("RX: %s" % rx)
            if rx != b"3\r":
                raise Exception("We want to set TL to 0x03 (TLS v1.2)")

            tx = b"$0 /flash/cert/aws.ca;/flash/cert/aws.crt;/flash/cert/aws.key\r"  # You can either use the absolute paths as shown, or else you can just specify the path relative to the /flash/cert directory, e.g.,: "AT$0 aws.ca;aws.crt;aws.key"
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("RX: %s" % rx)
            if rx != b"3\r":
                raise Exception("We want to set TL to 0x03 (TLS v1.2)")

            print("@todo tls")

            return  # @todo this is just temporary.

            # Switch to API Mode With Escapes.
            tx=b"ATAP2\r"
            ser.write(tx)
            print("TX: %s" % tx)
            time.sleep(2.0)
            rx = ser.read(1024)
            print("RX: %s" % rx)
            if rx != b'OK\r':
                raise Exception("Unable to put the device into API Mode!")
            
            # Exit out of AT Command Mode.
            tx=b"ATCN\r"
            ser.write(tx)
            print("TX: %s" % tx)
            time.sleep(2.0)
            rx = ser.read(1024)
            print("RX: %s" % rx)
            if rx != b'OK\r':
                raise Exception("Unable to exit out of AT Command Mode!")
            
            # *****
            # Now that we're in API Mode, it will be easier to perform
            # all the other device configuration because the message framing
            # is well-handled.
            # *****
            
            # Set the baud rate register to 7=115200 baud.
            tx = ATCommand(b"BD", b"\x07").packed  # Note that we don't use the ascii string "7" (i.e., ASCII 0x37); instead we use the binary value 0x07.
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("Got: %s" % rx)
            # Note: On error, you'd get this: b'~\x00\x05\x88\tBD\x01\xe7'
            # Note: On success, you get this: b'~\x00\x05\x88\tBD\x00\xe8'
            
            # Query the firmware version.
            tx = ATCommand(b"VR", b"").packed
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("Got: %s" % rx)
            
            # Query the verbose firmware version.
            tx = ATCommand(b"VL", b"").packed
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("Got: %s" % rx)
            
            # Query the hardware version.
            tx = ATCommand(b"HV", b"").packed
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("Got: %s" % rx)

            # Query the configuration CRC. This could be a quick way to detect an unexpected configuration change of the device.
            tx = ATCommand(b"CK", b"").packed
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("Got: %s" % rx)

            # Query the SHA256 hash of the MicroPython code.
            # Here's some examples of what this command retursn:
            #   ATFS HASH /flash/missing.txt
            #     ENOENT does not exist
            #   ATFS HASH /flash/cert/aws.key      (Note that this is a secure file! It works with secure files.)
            #     sha256 4b73b6c13523baaa1162e7a11e3299c8a0de84f003cc633d95af19d985514725
            #   ATFS HASH /flash/cert/aws.ca       (Note that this is NOT a secure file! It works with unsecure files.)
            #     sha256 870f56d009d8aeb95b716b0e7b0020225d542c4b283b9ed896edf97428d6712e
            #   ATFS HASH /flash/main.mpy (get SHA256 checksum of the micropython source file to verify that it has the correct file)
            #   (TBD)
            #
            # **UPDATE: Turns out you can't do this in API Frames Mode! We would have to do this in plain old AT Command Mode!**
            #   For more details, see [XBee3 Cellular User Guide](https://www.digi.com/resources/documentation/Digidocs/90002258/#Containers/cont_at_cmd_file_system.htm).
            #
            #tx = ATCommand(b"FS", b"HASH /flash/missing.txt").packed
            #ser.write(tx)
            #print("TX: %s" % tx)
            #rx = ser.read(1024)
            #print("Got: %s" % rx)
            # Note: On success, you'd get this: b'~\x00\x05\x88\tWR\x00\xc5'

            print("@todo Add more code here to set/get more parameters.")
            
            # Write all the configuration changes!pyth
            # @todo ATWR
            tx = ATCommand(b"WR", b"").packed
            ser.write(tx)
            print("TX: %s" % tx)
            rx = ser.read(1024)
            print("Got: %s" % rx)

            print("Done.")


    @staticmethod
    def test_deploy_firmware():
        '''
        We've compiled the xbee-anscic-library code into a Python module.
        Then we invoke it here, using PySerial to do the byte transfer.
        '''
        pass


def run_integration_tests():
    #IntegrationTests.test_api_user_data_relay()
    #IntegrationTests.test_api_AT_Command()
    #IntegrationTests.test_sockets_tcp()
    #IntegrationTests.test_sockets_tls()
    IntegrationTests.test_aws_connection()
    #IntegrationTests.test_dns_lookup_on_xbee()
    #IntegrationTests.test_api_tcp()
    #IntegrationTests.test_api_tls()
    #IntegrationTests.test_api_aws_connection()
    #IntegrationTests.test_detect_and_set_mode()
    #IntegrationTests.test_deploy_firmware()

    #TestPythonXBeeLibrary.test_get_parameter()
    #TestPythonXBeeLibrary.test_xbee_filesystem_commands()
    #TestPythonXBeeLibrary.test_aws_connection()
    #TestPythonXBeeLibrary.test_tcp()


if __name__ == "__main__":
    args = parse_arguments()
    if args.integration:
        print("Running the integration tests.")
        run_integration_tests()
    else:
        print("Running the unit tests.")
        unittest.main()
