# -*- coding: utf-8 -*-
from django import http
from django.conf import settings
from django.core.exceptions import PermissionDenied
from redsocks.redisstore import RedisStore, SELF
from redsocks.exceptions import WebSocketError, HandshakeError, UpgradeRequiredError
from redsocks import log

DEFAULT_CHANNELS = [
    'subscribe-session', 'subscribe-group', 'subscribe-user', 'subscribe-broadcast',
    'publish-session', 'publish-group', 'publish-user', 'publish-broadcast',
]


class RedisSubscriber(RedisStore):
    """ Subscriber class, used by the websocket code to listen for subscribed channels """
    subscription_channels = ['subscribe-session', 'subscribe-group', 'subscribe-user', 'subscribe-broadcast']
    publish_channels = ['publish-session', 'publish-group', 'publish-user', 'publish-broadcast']

    def __init__(self, connection):
        self.subscription = None
        super(RedisSubscriber, self).__init__(connection)

    def allowed_channels(self, request, channels):
        """ Can be used to restrict the subscription/publishing channels for the current client. This callback
            function shall return a list of allowed channels or throw a PermissionDenied exception.
        """
        return [c for c in channels if c in DEFAULT_CHANNELS]
        
    def get_file_descriptor(self):
        """ Return file descriptor used for select call when listening on message queue. """
        return self.subscription.connection and self.subscription.connection._sock.fileno()

    def parse_response(self):
        """ Parse a message response sent by the Redis datastore on a subscribed channel. """
        return self.subscription.parse_response()
        
    def set_pubsub_channels(self, request, channels):
        """ Initialize the channels used for publishing and subscribing messages through the message queue. """
        facility = request.path_info.replace(settings.WEBSOCKET_URL, '', 1)
        # initialize publishers
        audience = {
            'users': [SELF] if 'publish-user' in channels else [],
            'groups': [SELF] if 'publish-group' in channels else [],
            'sessions': [SELF] if 'publish-session' in channels else [],
            'broadcast': 'publish-broadcast' in channels,
        }
        self.publishers = set()
        for channel in self._iter_channels(facility, request, **audience):
            self.publishers.add(channel)
        # initialize subscribers
        audience = {
            'users': [SELF] if 'subscribe-user' in channels else [],
            'groups': [SELF] if 'subscribe-group' in channels else [],
            'sessions': [SELF] if 'subscribe-session' in channels else [],
            'broadcast': 'subscribe-broadcast' in channels,
        }
        self.subscription = self.client.pubsub()
        for channel in self._iter_channels(facility, request, **audience):
            self.subscription.subscribe(channel)

    def on_connect(self, request, websocket):
        """ This method is called immediately after a websocket is openend by the client. """
        # Send persisted messages upon connect..
        for channel in self.subscription.channels:
            message = self.client.get(channel)
            if message:
                websocket.send(message)
                
    def on_receive_message(self, request, websocket, message):
        return message
        
    def on_send_message(self, request, websocket, message):
        return message
        
    def on_error(self, request, websocket, err):
        log.error('Error: %s', err, exc_info=err)
        if isinstance(err, WebSocketError): return http.HttpResponse(status=1001, content='Websocket closed.')
        if isinstance(err, UpgradeRequiredError): return http.HttpResponseBadRequest(status=426, content=err)
        if isinstance(err, HandshakeError): return http.HttpResponseBadRequest(content=err)
        if isinstance(err, PermissionDenied): return http.HttpResponseForbidden(content=err)
        return http.HttpResponseServerError(content=err)

    def on_disconnect(self, request, websocket):
        """ New implementation to free up Redis subscriptions when websockets close. This prevents
            memory sap when Redis Output Buffer and Output Lists build when websockets are abandoned.
        """
        if self.subscription and self.subscription.subscribed:
            self.subscription.unsubscribe()
            self.subscription.reset()
