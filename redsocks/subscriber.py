# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import get_user
from django.utils.functional import SimpleLazyObject
from importlib import import_module
from redsocks.redisstore import RedisStore, SELF


class RedisSubscriber(RedisStore):
    """ Subscriber class, used by the websocket code to listen for subscribed channels """
    subscription_channels = ['subscribe-session', 'subscribe-group', 'subscribe-user', 'subscribe-broadcast']
    publish_channels = ['publish-session', 'publish-group', 'publish-user', 'publish-broadcast']

    def __init__(self, connection):
        self.subscription = None
        super(RedisSubscriber, self).__init__(connection)

    def allowed_channels(self, request, channels):
        """ Can be used to restrict the subscription/publishing channels for the current client. This callback
            function shall return a list of allowed channels or throw a ``PermissionDenied`` exception. Remember
            that this function is not allowed to perform any blocking requests, such as accessing the database!
        """
        return channels

    def process_request(self, request):
        request.session = None
        request.user = None
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        if session_key is not None:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore(session_key)
            request.user = SimpleLazyObject(lambda: get_user(request))

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

    def send_persited_messages(self, websocket):
        """ This method is called immediately after a websocket is openend by the client, so that
            persisted messages can be sent back to the client upon connection.
        """
        # TODO: REMOVE THIS FUNCTION?
        for channel in self.subscription.channels:
            message = self.client.get(channel)
            if message:
                websocket.send(message)

    def get_file_descriptor(self):
        """ Return file descriptor used for select call when listening on message queue. """
        return self.subscription.connection and self.subscription.connection._sock.fileno()

    def release(self):
        """ New implementation to free up Redis subscriptions when websockets close. This prevents
            memory sap when Redis Output Buffer and Output Lists build when websockets are abandoned.
        """
        if self.subscription and self.subscription.subscribed:
            self.subscription.unsubscribe()
            self.subscription.reset()
