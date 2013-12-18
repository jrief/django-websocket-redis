#-*- coding: utf-8 -*-
#!/Users/jrief/Workspace/virtualenvs/awesto/bin/uwsgi --virtualenv ~/Workspace/virtualenvs/awesto --http-socket :9090 --gevent 100 --module chat --http-websockets
#!./uwsgi --http-socket :9090 --gevent 100 --module tests.websocket_chat --gevent-monkey-patch
# uwsgi --virtualenv ~/Workspace/virtualenvs/awesto --http :9090 --http-raw-body --gevent 100 --module chat (läuft in ein timeout)
# uwsgi --virtualenv ~/Workspace/virtualenvs/awesto --http-socket :9090  --gevent 100 --module websocket --http-websockets (de-facto das gleiche wie --http)
# uwsgi --virtualenv ~/Workspace/virtualenvs/awesto --http :9090 --http-websockets --gevent 100 --module websocket
import uwsgi
import gevent.select
from ws4redis.exceptions import WebSocketError
from ws4redis.wsgi_server import WebsocketWSGIServer


class uWSGIWebsocket(object):
    def __init__(self):
        self._closed = False

    def get_file_descriptor(self):
        """Return the file descriptor for the given websocket"""
        try:
            return uwsgi.connection_fd()
        except IOError, e:
            self.close()
            raise WebSocketError(e)

    @property
    def closed(self):
        return self._closed

    def receive(self):
        if self._closed:
            raise WebSocketError("Connection is already closed")
        try:
            return uwsgi.websocket_recv_nb()
        except IOError, e:
            self.close()
            raise WebSocketError(e)

    def send(self, message, binary=None):
        try:
            uwsgi.websocket_send(message)
        except IOError, e:
            self.close()
            raise WebSocketError(e)

    def close(self, code=1000, message=''):
        self._closed = True


class uWSGIWebsocketServer(WebsocketWSGIServer):
    def upgrade_websocket(self, environ, start_response):
        uwsgi.websocket_handshake(environ['HTTP_SEC_WEBSOCKET_KEY'], environ.get('HTTP_ORIGIN', ''))
        return uWSGIWebsocket()

    def select(self, rlist, wlist, xlist, timeout=None):
        return gevent.select.select(rlist, wlist, xlist, timeout)
