#-*- coding: utf-8 -*-
import base64, hashlib, logging, select, six
from django.conf import settings
from django.core.management.commands import runserver
from django.core.servers.basehttp import WSGIServer, WSGIRequestHandler
from django.core.wsgi import get_wsgi_application
from django.utils.encoding import force_str
from django.utils.six.moves import socketserver
from redsocks.exceptions import HandshakeError, UpgradeRequiredError
from redsocks.runserver.websocket import WebSocket
from redsocks.uwsgiserver import uWSGIWebsocketServer
from wsgiref import util

log = logging.getLogger('django.request')
util._hoppish = {}.__contains__


class DjangoWebsocketServer(uWSGIWebsocketServer):
    WS_GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    WS_VERSIONS = ('13', '8', '7')
    
    def assert_websocket_requirements(self, websocket_version, key):
        # check websocket version
        if not websocket_version:
            raise UpgradeRequiredError()
        if websocket_version not in self.WS_VERSIONS:
            raise HandshakeError('Unsupported WebSocket Version: {0}'.format(websocket_version))
        # check websocket security key - 5.2.1 (3)
        if not key:
            raise HandshakeError('Sec-WebSocket-Key header is missing/empty')
        try:
            keylen = len(base64.b64decode(key))
            assert keylen == 16, TypeError()
        except TypeError:
            raise HandshakeError('Invalid key: {0}'.format(key))

    def upgrade_websocket(self, environ, start_response):
        """ Attempt to upgrade the socket environ['wsgi.input'] into a websocket enabled connection. """
        websocket_version = environ.get('HTTP_SEC_WEBSOCKET_VERSION', '')
        key = environ.get('HTTP_SEC_WEBSOCKET_KEY', '').strip()
        self.assert_websocket_requirements(websocket_version, key)
        sec_ws_accept = base64.b64encode(hashlib.sha1(six.b(key) + self.WS_GUID).digest())
        sec_ws_accept = sec_ws_accept.decode('ascii') if six.PY3 else sec_ws_accept
        headers = [
            ('Upgrade', 'websocket'),
            ('Connection', 'Upgrade'),
            ('Sec-WebSocket-Accept', sec_ws_accept),
            ('Sec-WebSocket-Version', str(websocket_version))
        ]
        if environ.get('HTTP_SEC_WEBSOCKET_PROTOCOL') is not None:
            headers.append(('Sec-WebSocket-Protocol', environ.get('HTTP_SEC_WEBSOCKET_PROTOCOL')))
        log.debug('WebSocket request accepted, switching protocols')
        start_response(force_str('101 Switching Protocols'), headers)
        six.get_method_self(start_response).finish_content()
        return WebSocket(environ['wsgi.input'])

    def select(self, rlist, wlist, xlist, timeout=None):
        return select.select(rlist, wlist, xlist, timeout)


def run(addr, port, wsgi_handler, ipv6=False, threading=False):
    """ Function to monkey patch the internal Django command: manage.py runserver """
    log.info('Websocket support is enabled')
    server_address = (addr, port)
    if not threading:
        raise Exception('Django Websocket server must run with threading enabled')
    httpd_cls = type('WSGIServer', (socketserver.ThreadingMixIn, WSGIServer), {'daemon_threads': True})
    httpd = httpd_cls(server_address, WSGIRequestHandler, ipv6=ipv6)
    httpd.set_app(wsgi_handler)
    httpd.serve_forever()
runserver.run = run


_django_app = get_wsgi_application()
_websocket_app = DjangoWebsocketServer()
_websocket_url = getattr(settings, 'WEBSOCKET_URL')


def application(environ, start_response):
    if _websocket_url and environ.get('PATH_INFO').startswith(_websocket_url):
        return _websocket_app(environ, start_response)
    return _django_app(environ, start_response)
