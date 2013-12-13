#-*- coding: utf-8 -*-
from socket import error as socket_error
from django.http import BadHeaderError


class WebSocketError(socket_error):
    """
    Raised when an active websocket encounters a problem.
    """


class FrameTooLargeException(WebSocketError):
    """
    Raised if a received frame is too large.
    """


class HandshakeError(BadHeaderError):
    """
    Raised if an error occurs during protocol handshake.
    """


class UpgradeRequiredError(HandshakeError):
    """
    Raised if protocol must be upgraded.
    """
