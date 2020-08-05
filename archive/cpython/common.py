import binascii
import socket
import struct


# TODO Really need to clean up the interface to my API frame packing classes.
#  For example, "self.packed" as public interface is awful.


def require_type_bytes(data):
    '''
    @throws A TypeError if the given argument is not of type 'bytes'.
    @note Do NOT structure your code to catch this exception as a way to check for invalid input.
    In practice, you should NEVER allow this method to throw an exception. Exceptions are for
    truly unexpected, unavoidable circumstances. If this exception occurs, shame on you because
    you disobeyed the docs and didn't pass the correct type into the function.
    '''
    if not isinstance(data, bytes):
        raise TypeError("Expected <class 'bytes'> but got %s." % type(data))


def dotted_quad_to_bytes(ip_string):
    '''
    https://stackoverflow.com/questions/9590965/convert-an-ip-string-to-a-number-and-vice-versa
    https://docs.python.org/3/library/socket.html#socket.inet_aton
    '''
    return socket.inet_aton(ip_string)


def to_hex(data):
    """
    @returns An ascii string containing the data.
    """
    #return binascii.hexlify(data)
    return " ".join(["%02X" % i for i in data])


class APIFrame:
    def __init__(self, frame_data):
        '''
        @param frame_data The message payload, of type 'bytes' (i.e., NOT 'str').
        '''
        require_type_bytes(frame_data)
        self.START_CHAR = b'\x7E'
        self.frame_data_len = struct.pack('>H', len(frame_data))  # Pack into a uint16. The '>' indicates big-endian byte order.
        self.packed = self.START_CHAR + APIFrame.escape( self.frame_data_len + frame_data + self.calculate_checksum(frame_data) )

    def __repr__(self):
        ''' Overridden to facilitate logging. '''
        return "APIFrame(hex=%s, len=%s)" % (to_hex(self.packed), self.frame_data_len)

    @staticmethod
    def calculate_checksum(frame_data):
        '''
        @param frame_data The packet payload. Does not include start character, length, or checksum bytes.
        @returns The checksum for the given message.
        '''
        require_type_bytes(frame_data)
        checksum = 0
        for c in frame_data:
            checksum += c           # Add all bytes
        checksum &= 0xFF            # Keep only the lowest 8 bits.
        checksum = 0xFF - checksum  # Subtract quantity from 0xFF.
        return bytes([checksum])    # https://stackoverflow.com/questions/21017698/converting-int-to-bytes-in-python-3

    @staticmethod
    def verify_checksum(frame_data_and_checksum):
        '''
        @param frame_data_and_checksum The packet payload along with checksum character. Does not include start character or length bytes. Assumes input is of type "bytes".
        @returns True IFF the checksum for the given message is correct.
        '''
        require_type_bytes(frame_data_and_checksum)
        checksum = 0
        for c in frame_data_and_checksum:
            checksum += c
        checksum &= 0xFF  # Keep only the lowest byte.
        return checksum == 0xFF

    @staticmethod
    def escape(msg):
        '''
        @returns the escaped version of the messages.
        '''
        require_type_bytes(msg)
        CHARS_TO_ESCAPE = b'\x7E\x7D\x11\x13'  # Start character, escape character, XON, XOFF (respectively)
        ESCAPE_CHAR = 0x7D
        escaped_msg = []
        for c in msg:
            if c in CHARS_TO_ESCAPE:
                escaped_msg.append(ESCAPE_CHAR)
                escaped_msg.append(c ^ 0x20)
            else:
                escaped_msg.append(c)
        return bytes(escaped_msg)


class ATCommand:
    def __init__(self, command, params):
        require_type_bytes(command)
        require_type_bytes(params)
        assert 2 == len(command)
        frame_type = b'\x08'
        frame_id = b'\x09'  # Don't leave frame ID as the value zero; if you do, you won't get a response! I just arbitrarily chose the value 0x09 at random.
        
        frame_data = frame_type + frame_id + command + params
        
        self.packed = APIFrame(frame_data).packed

    def __repr__(self):
        ''' Overridden to facilitate logging. '''
        return "ATCommand(bytes=%s, hex=%s)" % (self.packed, to_hex(self.packed))


class TXRequest:
    def __init__(self, payload, dst, tls_profile=None, tls_port=443):
        '''
        @param payload The byte string to send.
        @param dst The destination address
        '''
        require_type_bytes(payload)

        frame_id = b'\x01'                    # Don't want to use zero for the frame ID because otherwise we won't get a tx status frame.
        dst_addr = dotted_quad_to_bytes(dst)  # Convert to a uint32 in network byte order (big endian)
        src_port = struct.pack('>H', 0)       # Use zero so that it automatically selects the port.
        tx_options = b'\x00'                  # 0=Leave socket open, 1=close after transmission.

        if tls_profile:

            USE_BASIC_TX_REQUEST = True       # Selects between the two different types of API Frames that could be used to send the TCP+SSL/TLS message.

            if USE_BASIC_TX_REQUEST and tls_profile == b'\x00':  # Notice that if you are using some profile other than $0, you don't get a choice, it will force you to use API Frame Type 0x23.
                # ----- TX REQUEST IPV4 (API FRAME TYPE 0x20) -----
                frame_type = b'\x20'          # TX Request API frame.
                dst_port = struct.pack('>H', tls_port)  # Pack into a uint16. The '>' indicates big-endian byte order.
                protocol = b'\x04'            # 0=UDP, 1=TCP, 4=SSL/TLS Profile 0
                frame_data = frame_type + frame_id + dst_addr + dst_port + src_port + protocol + tx_options + payload
            else:
                # ----- TX REQUEST WITH TLS PROFILE (API FRAME TYPE 0x23) -----
                frame_type = b'\x23'          # TX Request with TLS Profile API frame.
                dst_port = struct.pack('>H', tls_port) # Pack into a uint16. The '>' indicates big-endian byte order.
                frame_data = frame_type + frame_id + dst_addr + dst_port + src_port + tls_profile + tx_options + payload

        else:
            frame_type = b'\x20'              # TX Request API frame.
            dst_port = struct.pack('>H', 80)  # Pack into a uint16. The '>' indicates big-endian byte order.
            protocol = b'\x01'                # 0=UDP, 1=TCP, 4=SSL/TLS Profile 0
            frame_data = frame_type + frame_id + dst_addr + dst_port + src_port + protocol + tx_options + payload

        self.tls_profile = tls_profile
        self.frame_type = to_hex(frame_type)
        self.dst = dst
        self.dst_port = struct.unpack('>H', dst_port)[0]
        self.packed = APIFrame(frame_data).packed

    def __repr__(self):
        ''' Overridden to facilitate logging. '''
        return "TXRequest(isTLS=%s, frame_type=0x%s, dst=%s, dst_port=%s(base10), bytes=%s, hex=%s)" % (self.tls_profile is not None, self.frame_type, self.dst, self.dst_port, self.packed, to_hex(self.packed))


class UserDataRelay:
    def __init__(self, user_data):
        require_type_bytes(user_data)

        frame_type = b'\x2D'
        frame_id = b'\x00'
        destination_interface = b'\x02' # MicroPython

        frame_data = frame_type + frame_id + destination_interface + user_data

        self.packed = APIFrame(frame_data).packed

    def __repr__(self):
        ''' Overridden to facilitate logging. '''
        return "UserDataRelay(hex=%s)" % to_hex(self.packed)
