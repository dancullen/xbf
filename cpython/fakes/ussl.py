""" ussl.py is an implementation of the MicroPython ussl interface that uses the CPython3 ssl module. """

class WrappedSocket:

    def __init__(self, s, keyfile=None, certfile=None, ca_certs=None, server_side=False, server_hostname=None):
        import ssl
        self.wrap = ssl.wrap_socket(s.sock,
                                    keyfile=keyfile, certfile=certfile, ca_certs=ca_certs,
                                    cert_reqs=ssl.CERT_REQUIRED)

    def connect(self, address):
        return self.wrap.connect(address)

    def shutdown(self, how):
        return self.wrap.shutdown(how)

    def close(self):
        return self.wrap.close()

    def setblocking(self, flag):
        return self.wrap.setblocking(flag)

    def settimeout(self, value):
        return self.wrap.settimeout(value)

    def read(self, size):
        # In MicroPython, socket.read() returns None if the socket is nonblocking and no data is available.
        # However, in CPython3, socket.read() raises an exception if no data is available.
        # Since this file contains the CPython3 implementation, we need to catch the exception
        # and return None in order to make this behave like the MicroPython version.
        try:
            ret = self.wrap.read(size)
        except Exception as ex:
            ret = None
        return ret

    def write(self, buf, num=None):
        if num is None:
            num = len(buf)
        return self.wrap.write(buf[:num])


def wrap_socket(sock, keyfile=None, certfile=None, ca_certs=None, server_side=False, server_hostname=None):
    return WrappedSocket(sock,
                         keyfile=keyfile, certfile=certfile, ca_certs=ca_certs,
                         server_side=server_side, server_hostname=server_hostname)
