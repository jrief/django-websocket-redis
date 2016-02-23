# -*- coding: utf-8 -*-
import uwsgi
import gevent.select
from redsocks.exceptions import WebSocketError
from redsocks.server.wsgi import WSGIWebsocketServer


def close_on_ioerror(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except IOError as err:
            self.closed = True
            raise WebSocketError(err)
    return wrapper


class uWSGIWebsocket(object):
    def __init__(self):
        self.closed = False

    @close_on_ioerror
    def get_file_descriptor(self):
        return uwsgi.connection_fd()

    @close_on_ioerror
    def receive(self):
        if self.closed:
            raise WebSocketError('Connection is already closed')
        return uwsgi.websocket_recv_nb()

    @close_on_ioerror
    def flush(self):
        uwsgi.websocket_recv_nb()
            
    @close_on_ioerror
    def send(self, message, binary=None):
        uwsgi.websocket_send(message)

    def close(self, *args, **kwargs):
        self.closed = True


class uWSGIWebsocketServer(WSGIWebsocketServer):
    def upgrade_websocket(self, environ, start_response):
        uwsgi.websocket_handshake(environ['HTTP_SEC_WEBSOCKET_KEY'], environ.get('HTTP_ORIGIN', ''))
        return uWSGIWebsocket()

    def select(self, rlist, wlist, xlist, timeout=None):
        return gevent.select.select(rlist, wlist, xlist, timeout)
