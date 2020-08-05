""" usocket.py is an implementation of the MicroPython socket interface that uses the CPython3 socket module. """

import socket as cpython3_socket

AF_INET = cpython3_socket.AF_INET
AF_INET6 = cpython3_socket.AF_INET6
SOCK_STREAM = cpython3_socket.SOCK_STREAM
SOCK_DGRAM = cpython3_socket.SOCK_DGRAM
IPPROTO_IP = cpython3_socket.IPPROTO_IP
IPPROTO_UDP = cpython3_socket.IPPROTO_UDP
IPPROTO_TCP = cpython3_socket.IPPROTO_TCP
IPPROTO_SEC = cpython3_socket.IPPROTO_TCP  # CPython3 doesn't define IPPROTO_SEC. Use a regular TCP protocol instead.


class socket:

    def __init__(self, af=AF_INET, type=SOCK_STREAM, proto=IPPROTO_TCP):
        self.sock = cpython3_socket.socket(family=af, type=type, proto=proto)
        self.fail = False

    def connect(self, address):
        if self.fail:
            raise Exception("Fake connect error")
        return self.sock.connect(address)

    def shutdown(self, how):
        return self.sock.shutdown(how)

    def close(self):
        return self.sock.close()

    def setblocking(self, flag):
        return self.sock.setblocking(flag)

    def settimeout(self, value):
        return self.sock.settimeout(value)

    def read(self, size):
        # https://docs.python.org/3/library/socket.html - "Note that there are no methods
        # read() or write(); use recv() and send() without flags argument instead."
        #
        # The Digi XBee MicroPython TCP socket returns None when no data is available for non-blocking TCP sockets.
        # This disagrees with CPython3 sockets, which instead throw an ETIMEDOUT or EAGAIN exception if no data
        # is available.
        #
        # In standard MicroPython, socket.read() returns None if the TCP socket is nonblocking and no data is available.
        # However, in CPython3, socket.recv() raises an exception if no data is available.
        # Since this file contains the CPython3 implementation, we need to catch the exception
        # and return None in order to make this behave like the MicroPython version.
        if self.fail:
            raise Exception("Fake read error")
        try:
            ret = self.sock.recv(size)
        except Exception as ex:
            ret = None
        return ret

    def write(self, buf, num=None):
        # https://docs.python.org/3/library/socket.html - "Note that there are no methods
        # read() or write(); use recv() and send() without flags argument instead."
        #
        # Notice that there is an optional second argument that indicates the number of bytes that should be written
        # from the buffer (None indicates that entire buffer should be written). According to the note at the top of
        # https://docs.micropython.org/en/latest/library/usocket.html, this is the case because MicroPython socket
        # objects are also stream objects. In CPython3, however, this is not the case-- socket.write() does NOT
        # take a second argument. However, this implementation of usocket MUST support the second argument because
        # umqtt.py and potentially other MicroPython code relies upon it.

        if self.fail:
            raise Exception("Fake write error")
        if num is None:
            num = len(buf)
        return self.sock.send(buf[:num])

    def sendto(self, buf, addr):
        if self.fail:
            raise Exception("Fake sendto error")
        return self.sock.sendto(buf, addr)

    def recvfrom(self, size):
        # The Digi XBee MicroPython UDP socket throws an exception (OSError "ETIMEDOUT" or "EAGAIN")
        # when no data is available for non-blocking UDP sockets. This agrees with CPython3, so don't catch
        # the CPython3 exception and instead allow it to pass up the call stack.
        #
        # Note that this behavior is inconsistent with MicroPython socket.read() for TCP sockets--
        # see comments above under read() for more details.
        if self.fail:
            raise Exception("Fake recvfrom error")
        return self.sock.recvfrom(size)
