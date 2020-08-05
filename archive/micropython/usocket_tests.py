# Note: A better, more-up-to-date example of usocket/ussl/etc. can be found in lps/common/test.py.


# Note: https://docs.micropython.org/en/latest/library/usocket.html
# Note: Error codes are defined in here:  https://github.com/micropython/micropython-lib/blob/master/errno/errno.py
#       So when socket.send() throws an error code, for example, that's where you look.

def http_get(url):
    import usocket

    scheme, _, host, path = url.split('/', 3)
    print("GOT HOST: %s" % host)

    try:
        addr = usocket.getaddrinfo(host, 80)[0][-1]
        s = usocket.socket()
        s.connect(addr)
        request=bytes('GET /%s HTTP/1.1\r\nHost: %s\r\n\r\n' % (path, host), 'utf8')
        print("Requesting /%s from host %s\n" % (path, host))
        s.send(request)
        while True:
            print(str(s.recv(500), 'utf8'), end = '')
    finally:
        s.close()


def test_https():
    import usocket
    import ussl

    THING = b'CS-XBee'

    HOST = "api.ipify.org"
    PORT = 443
    tx = b'GET / HTTP/1.1\r\nHost: %s\r\nUser-Agent: curl/7.64.0\r\nAccept: */*\r\n\r\n' % HOST

    #HOST = "a346ga75b9eiwl-ats.iot.us-west-2.amazonaws.com"
    #PORT = 8443
    #tx = b'GET /things/%s/shadow HTTP/1.0\r\nHost: %s\r\n\r\n' % (THING, HOST)

    addr = usocket.getaddrinfo(HOST, 80)[0][-1]

    sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)

    key_file = 'cert/aws.key.der'
    cert_file = 'cert/aws.ca.der'
    
    with open(key_file, 'rb') as f:
       key_data = f.read()

    with open(cert_file, 'rb') as f:
        cert_data = f.read()

    #print("key_data: %s" % key_data)
    #print("cert_data: %s" % cert_data)

    #print("Attempting to connect...")
    #sock.connect(addr)
    #print("Connected.")

    print("Wrapping...")
    wrap = ussl.wrap_socket(sock, key=key_data, cert=cert_data)
    print("Done wrapping.")

    wrap.settimeout(10)

    print("Attempting to connect...")
    wrap.connect(addr)
    print("Connected.")

    wrap.write(tx)
    print("Transmitted: %s" % tx)

    rx = str(wrap.read(1024), 'utf-8')
    print("Received: %s" % rx)

    wrap.shutdown(usocket.SHUT_RDWR)
    wrap.close()


if __name__ == "__main__":
    # http_get('http://www.micropython.org/ks/test.html')
    test_https()
