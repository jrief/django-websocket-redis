#-*- coding: utf-8 -*-
import six
import base64
import select
import logging
from hashlib import sha1
from wsgiref import util
from django.core.wsgi import get_wsgi_application
from django.core.servers.basehttp import WSGIServer, ServerHandler as _ServerHandler, WSGIRequestHandler as _WSGIRequestHandler
from django.conf import settings
from django.core.management.commands import runserver
from django.utils.six.moves import socketserver
from django.utils.encoding import force_str
from ws4redis.websocket import WebSocket
from ws4redis.wsgi_server import WebsocketWSGIServer, HandshakeError, UpgradeRequiredError

util._hoppish = {}.__contains__
logger = logging.getLogger('django.request')


class ServerHandler(_ServerHandler):
    http_version = str("1.1")

class WSGIRequestHandler(_WSGIRequestHandler):
    protocol_version = 'HTTP/1.1'

    def handle(self):
        """Handle multiple requests if necessary."""
        self.close_connection = 1

        self.handle_one_request()

    def handle_one_request(self):
        """Copy of WSGIRequestHandler.handle(), but with different ServerHandler"""
        """Copy of WSGIRequestHandler, but with different ServerHandler"""

        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        if not self.parse_request():  # An error code has been sent, just exit
            return

        handler = ServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        )
        handler.request_handler = self      # backpointer for logging
        handler.run(self.server.get_app())


class WebsocketRunServer(WebsocketWSGIServer):
    WS_GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    WS_VERSIONS = ('13', '8', '7')
    protocol_version = "HTTP/1.1"

    def upgrade_websocket(self, environ, start_response):
        """
        Attempt to upgrade the socket environ['wsgi.input'] into a websocket enabled connection.
        """
        websocket_version = environ.get('HTTP_SEC_WEBSOCKET_VERSION', '')
        if not websocket_version:
            raise UpgradeRequiredError
        elif websocket_version not in self.WS_VERSIONS:
            raise HandshakeError('Unsupported WebSocket Version: {0}'.format(websocket_version))

        key = environ.get('HTTP_SEC_WEBSOCKET_KEY', '').strip()
        if not key:
            raise HandshakeError('Sec-WebSocket-Key header is missing/empty')
        try:
            key_len = len(base64.b64decode(key))
        except TypeError:
            raise HandshakeError('Invalid key: {0}'.format(key))
        if key_len != 16:
            # 5.2.1 (3)
            raise HandshakeError('Invalid key: {0}'.format(key))

        sec_ws_accept = base64.b64encode(sha1(six.b(key) + self.WS_GUID).digest())
        if six.PY3:
            sec_ws_accept = sec_ws_accept.decode('ascii')
        headers = [
            ('Upgrade', 'websocket'),
            ('Connection', 'Upgrade'),
            ('Sec-WebSocket-Accept', sec_ws_accept),
            ('Sec-WebSocket-Version', str(websocket_version))
        ]
        if environ.get('HTTP_SEC_WEBSOCKET_PROTOCOL') is not None:
            headers.append(('Sec-WebSocket-Protocol', environ.get('HTTP_SEC_WEBSOCKET_PROTOCOL')))

        logger.debug('WebSocket request accepted, switching protocols')
        start_response(force_str('101 Switching Protocols'), headers)
        six.get_method_self(start_response).finish_content()
        return WebSocket(environ['wsgi.input'])

    def select(self, rlist, wlist, xlist, timeout=None):
        return select.select(rlist, wlist, xlist, timeout)


def run(addr, port, wsgi_handler, ipv6=False, threading=False, **kwargs):
    """
    Function to monkey patch the internal Django command: manage.py runserver
    """
    logger.info('Websocket support is enabled')
    server_address = (addr, port)
    if not threading:
        raise Exception("Django's Websocket server must run with threading enabled")
    httpd_cls = type('WSGIServer', (socketserver.ThreadingMixIn, WSGIServer), {'daemon_threads': True})
    httpd = httpd_cls(server_address, WSGIRequestHandler, ipv6=ipv6)
    httpd.set_app(wsgi_handler)
    httpd.serve_forever()
runserver.run = run


_django_app = get_wsgi_application()
_websocket_app = WebsocketRunServer()
_websocket_url = getattr(settings, 'WEBSOCKET_URL')


def application(environ, start_response):
    if _websocket_url and environ.get('PATH_INFO').startswith(_websocket_url):
        return _websocket_app(environ, start_response)
    return _django_app(environ, start_response)
