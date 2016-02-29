# -*- coding: utf-8 -*-
import uwsgi
from redsocks.exceptions import WebSocketError


class uWSGIWebsocket(object):
    def __init__(self):
        self.closed = False

    def get_file_descriptor(self):
        try:
            return uwsgi.connection_fd()
        except IOError as err:
            self.close(err=err)

    def receive(self):
        try:
            if self.closed:
                raise WebSocketError('Connection is already closed')
            return uwsgi.websocket_recv_nb()
        except IOError as err:
            self.close(err=err)

    def flush(self):
        try:
            uwsgi.websocket_recv_nb()
        except IOError as err:
            self.close(err=err)
            
    def send(self, message, binary=None):
        try:
            uwsgi.websocket_send(message)
        except IOError as err:
            self.close(err=err)

    def close(self, *args, **kwargs):
        self.closed = True
        if kwargs.get('err'):
            raise WebSocketError(kwargs['err'])
