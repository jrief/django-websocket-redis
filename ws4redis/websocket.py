# -*- coding: utf-8 -*-
# This code was generously pilfered from https://bitbucket.org/Jeffrey/gevent-websocket
# written by Jeffrey Gelens (http://noppo.pro/) and licensed under the Apache License, Version 2.0
import logging
import six
import struct
from socket import error as socket_error
from ws4redis.utf8validator import Utf8Validator
from ws4redis.exceptions import WebSocketError, FrameTooLargeException

logger = logging.getLogger('django.request')

if six.PY3:
    xrange = range


class WebSocket(object):
    __slots__ = ('_closed', 'stream', 'utf8validator', 'utf8validate_last')

    OPCODE_CONTINUATION = 0x00
    OPCODE_TEXT = 0x01
    OPCODE_BINARY = 0x02
    OPCODE_CLOSE = 0x08
    OPCODE_PING = 0x09
    OPCODE_PONG = 0x0a

    def __init__(self, wsgi_input):
        self._closed = False
        self.stream = Stream(wsgi_input)
        self.utf8validator = Utf8Validator()
        self.utf8validate_last = None

    def __del__(self):
        try:
            self.close()
        except:
            # close() may fail if __init__ didn't complete
            pass

    def _decode_bytes(self, bytestring):
        """
        Internal method used to convert the utf-8 encoded bytestring into unicode.
        If the conversion fails, the socket will be closed.
        """
        if not bytestring:
            return u''
        try:
            return bytestring.decode('utf-8')
        except UnicodeDecodeError:
            self.close(1007)
            raise

    def _encode_bytes(self, text):
        """
        :returns: The utf-8 byte string equivalent of `text`.
        """
        if isinstance(text, six.binary_type):
            return text
        if not isinstance(text, six.text_type):
            text = six.text_type(text or '')
        return text.encode('utf-8')

    def _is_valid_close_code(self, code):
        """
        :returns: Whether the returned close code is a valid hybi return code.
        """
        if code < 1000:
            return False
        if 1004 <= code <= 1006:
            return False
        if 1012 <= code <= 1016:
            return False
        if code == 1100:
            # not sure about this one but the autobahn fuzzer requires it.
            return False
        if 2000 <= code <= 2999:
            return False
        return True

    def get_file_descriptor(self):
        """Return the file descriptor for the given websocket"""
        return self.stream.fileno

    @property
    def closed(self):
        return self._closed

    def handle_close(self, header, payload):
        """
        Called when a close frame has been decoded from the stream.

        :param header: The decoded `Header`.
        :param payload: The bytestring payload associated with the close frame.
        """
        if not payload:
            self.close(1000, None)
            return
        if len(payload) < 2:
            raise WebSocketError('Invalid close frame: {0} {1}'.format(header, payload))
        rv = payload[:2]
        if six.PY2:
            code = struct.unpack('!H', str(rv))[0]
        else:
            code = struct.unpack('!H', bytes(rv))[0]
        payload = payload[2:]
        if payload:
            validator = Utf8Validator()
            val = validator.validate(payload)
            if not val[0]:
                raise UnicodeError
        if not self._is_valid_close_code(code):
            raise WebSocketError('Invalid close code {0}'.format(code))
        self.close(code, payload)

    def handle_ping(self, header, payload):
        self.send_frame(payload, self.OPCODE_PONG)

    def handle_pong(self, header, payload):
        pass

    def read_frame(self):
        """
        Block until a full frame has been read from the socket.

        This is an internal method as calling this will not cleanup correctly
        if an exception is called. Use `receive` instead.

        :return: The header and payload as a tuple.
        """
        header = Header.decode_header(self.stream)
        if header.flags:
            raise WebSocketError
        if not header.length:
            return header, ''
        try:
            payload = self.stream.read(header.length)
        except socket_error:
            payload = ''
        except Exception:
            logger.debug("{}: {}".format(type(e), six.text_type(e)))
            payload = ''
        if len(payload) != header.length:
            raise WebSocketError('Unexpected EOF reading frame payload')
        if header.mask:
            payload = header.unmask_payload(payload)
        return header, payload

    def validate_utf8(self, payload):
        # Make sure the frames are decodable independently
        self.utf8validate_last = self.utf8validator.validate(payload)

        if not self.utf8validate_last[0]:
            raise UnicodeError("Encountered invalid UTF-8 while processing "
                               "text message at payload octet index "
                               "{0:d}".format(self.utf8validate_last[3]))

    def read_message(self):
        """
        Return the next text or binary message from the socket.

        This is an internal method as calling this will not cleanup correctly
        if an exception is called. Use `receive` instead.
        """
        opcode = None
        message = None
        while True:
            header, payload = self.read_frame()
            f_opcode = header.opcode
            if f_opcode in (self.OPCODE_TEXT, self.OPCODE_BINARY):
                # a new frame
                if opcode:
                    raise WebSocketError("The opcode in non-fin frame is expected to be zero, got {0!r}".format(f_opcode))
                # Start reading a new message, reset the validator
                self.utf8validator.reset()
                self.utf8validate_last = (True, True, 0, 0)
                opcode = f_opcode
            elif f_opcode == self.OPCODE_CONTINUATION:
                if not opcode:
                    raise WebSocketError("Unexpected frame with opcode=0")
            elif f_opcode == self.OPCODE_PING:
                self.handle_ping(header, payload)
                continue
            elif f_opcode == self.OPCODE_PONG:
                self.handle_pong(header, payload)
                continue
            elif f_opcode == self.OPCODE_CLOSE:
                self.handle_close(header, payload)
                return
            else:
                raise WebSocketError("Unexpected opcode={0!r}".format(f_opcode))
            if opcode == self.OPCODE_TEXT:
                self.validate_utf8(payload)
                if six.PY3:
                    payload = payload.decode()
            if message is None:
                message = six.text_type() if opcode == self.OPCODE_TEXT else six.binary_type()
            message += payload
            if header.fin:
                break
        if opcode == self.OPCODE_TEXT:
            if six.PY2:
                self.validate_utf8(message)
            else:
                self.validate_utf8(message.encode())
            return message
        else:
            return bytearray(message)

    def receive(self):
        """
        Read and return a message from the stream. If `None` is returned, then
        the socket is considered closed/errored.
        """
        if self._closed:
            raise WebSocketError("Connection is already closed")
        try:
            return self.read_message()
        except UnicodeError as e:
            logger.info('websocket.receive: UnicodeError {}'.format(e))
            self.close(1007)
        except WebSocketError as e:
            logger.info('websocket.receive: WebSocketError {}'.format(e))
            self.close(1002)
        except Exception as e:
            logger.info('websocket.receive: Unknown error {}'.format(e))
            raise e

    def flush(self):
        """
        Flush a websocket. In this implementation intentionally it does nothing.
        """
        pass

    def send_frame(self, message, opcode):
        """
        Send a frame over the websocket with message as its payload
        """
        if self._closed:
            raise WebSocketError("Connection is already closed")
        if opcode == self.OPCODE_TEXT:
            message = self._encode_bytes(message)
        elif opcode == self.OPCODE_BINARY:
            message = six.binary_type(message)
        header = Header.encode_header(True, opcode, '', len(message), 0)
        try:
            self.stream.write(header + message)
        except socket_error:
            raise WebSocketError("Socket is dead")

    def send(self, message, binary=False):
        """
        Send a frame over the websocket with message as its payload
        """
        if binary is None:
            binary = not isinstance(message, six.string_types)
        opcode = self.OPCODE_BINARY if binary else self.OPCODE_TEXT
        try:
            self.send_frame(message, opcode)
        except WebSocketError:
            raise WebSocketError("Socket is dead")

    def close(self, code=1000, message=''):
        """
        Close the websocket and connection, sending the specified code and
        message.  The underlying socket object is _not_ closed, that is the
        responsibility of the initiator.
        """
        try:
            message = self._encode_bytes(message)
            self.send_frame(
                struct.pack('!H%ds' % len(message), code, message),
                opcode=self.OPCODE_CLOSE)
        except WebSocketError:
            # Failed to write the closing frame but it's ok because we're
            # closing the socket anyway.
            logger.debug("Failed to write closing frame -> closing socket")
        finally:
            logger.debug("Closed WebSocket")
            self._closed = True
            self.stream = None


class Stream(object):
    """
    Wraps the handler's socket/rfile attributes and makes it in to a file like
    object that can be read from/written to by the lower level websocket api.
    """

    __slots__ = ('read', 'write', 'fileno')

    def __init__(self, wsgi_input):
        if six.PY2:
            self.read = wsgi_input._sock.recv
            self.write = wsgi_input._sock.sendall
        else:
            self.read = wsgi_input.raw._sock.recv
            self.write = wsgi_input.raw._sock.sendall
        self.fileno = wsgi_input.fileno()


class Header(object):
    __slots__ = ('fin', 'mask', 'opcode', 'flags', 'length')

    FIN_MASK = 0x80
    OPCODE_MASK = 0x0f
    MASK_MASK = 0x80
    LENGTH_MASK = 0x7f
    RSV0_MASK = 0x40
    RSV1_MASK = 0x20
    RSV2_MASK = 0x10

    # bitwise mask that will determine the reserved bits for a frame header
    HEADER_FLAG_MASK = RSV0_MASK | RSV1_MASK | RSV2_MASK

    def __init__(self, fin=0, opcode=0, flags=0, length=0):
        self.mask = ''
        self.fin = fin
        self.opcode = opcode
        self.flags = flags
        self.length = length

    def mask_payload(self, payload):
        payload = bytearray(payload)
        mask = bytearray(self.mask)
        for i in xrange(self.length):
            payload[i] ^= mask[i % 4]
        if six.PY3:
            return bytes(payload)
        return str(payload)

    # it's the same operation
    unmask_payload = mask_payload

    def __repr__(self):
        return ("<Header fin={0} opcode={1} length={2} flags={3} at "
                "0x{4:x}>").format(self.fin, self.opcode, self.length,
                                   self.flags, id(self))

    @classmethod
    def decode_header(cls, stream):
        """
        Decode a WebSocket header.

        :param stream: A file like object that can be 'read' from.
        :returns: A `Header` instance.
        """
        read = stream.read
        data = read(2)
        if len(data) != 2:
            raise WebSocketError("Unexpected EOF while decoding header")
        first_byte, second_byte = struct.unpack('!BB', data)
        header = cls(
            fin=first_byte & cls.FIN_MASK == cls.FIN_MASK,
            opcode=first_byte & cls.OPCODE_MASK,
            flags=first_byte & cls.HEADER_FLAG_MASK,
            length=second_byte & cls.LENGTH_MASK)
        has_mask = second_byte & cls.MASK_MASK == cls.MASK_MASK
        if header.opcode > 0x07:
            if not header.fin:
                raise WebSocketError('Received fragmented control frame: {0!r}'.format(data))
            # Control frames MUST have a payload length of 125 bytes or less
            if header.length > 125:
                raise FrameTooLargeException('Control frame cannot be larger than 125 bytes: {0!r}'.format(data))
        if header.length == 126:
            # 16 bit length
            data = read(2)
            if len(data) != 2:
                raise WebSocketError('Unexpected EOF while decoding header')
            header.length = struct.unpack('!H', data)[0]
        elif header.length == 127:
            # 64 bit length
            data = read(8)
            if len(data) != 8:
                raise WebSocketError('Unexpected EOF while decoding header')
            header.length = struct.unpack('!Q', data)[0]
        if has_mask:
            mask = read(4)
            if len(mask) != 4:
                raise WebSocketError('Unexpected EOF while decoding header')
            header.mask = mask
        return header

    @classmethod
    def encode_header(cls, fin, opcode, mask, length, flags):
        """
        Encodes a WebSocket header.

        :param fin: Whether this is the final frame for this opcode.
        :param opcode: The opcode of the payload, see `OPCODE_*`
        :param mask: Whether the payload is masked.
        :param length: The length of the frame.
        :param flags: The RSV* flags.
        :return: A bytestring encoded header.
        """
        first_byte = opcode
        second_byte = 0
        if six.PY2:
            extra = ''
        else:
            extra = b''
        if fin:
            first_byte |= cls.FIN_MASK
        if flags & cls.RSV0_MASK:
            first_byte |= cls.RSV0_MASK
        if flags & cls.RSV1_MASK:
            first_byte |= cls.RSV1_MASK
        if flags & cls.RSV2_MASK:
            first_byte |= cls.RSV2_MASK
        # now deal with length complexities
        if length < 126:
            second_byte += length
        elif length <= 0xffff:
            second_byte += 126
            extra = struct.pack('!H', length)
        elif length <= 0xffffffffffffffff:
            second_byte += 127
            extra = struct.pack('!Q', length)
        else:
            raise FrameTooLargeException
        if mask:
            second_byte |= cls.MASK_MASK
            extra += mask
        if six.PY3:
            return bytes([first_byte, second_byte]) + extra
        return chr(first_byte) + chr(second_byte) + extra
