# -*- coding: utf-8 -*-
from django.conf import settings
from redsocks.redis_store import RedisStore, SELF


class RedisSubscriber(RedisStore):
    """
    Subscriber class, used by the websocket code to listen for subscribed channels
    """
    subscription_channels = ['subscribe-session', 'subscribe-group', 'subscribe-user', 'subscribe-broadcast']
    publish_channels = ['publish-session', 'publish-group', 'publish-user', 'publish-broadcast']

    def __init__(self, connection):
        self._subscription = None
        super(RedisSubscriber, self).__init__(connection)

    def allowed_channels(self, request, channels):
        """
        Can be used to restrict the subscription/publishing channels for the current client. This callback
        function shall return a list of allowed channels or throw a ``PermissionDenied`` exception. Remember
        that this function is not allowed to perform any blocking requests, such as accessing the database!
        """
        return channels

    def parse_response(self):
        """
        Parse a message response sent by the Redis datastore on a subscribed channel.
        """
        return self._subscription.parse_response()

    def set_pubsub_channels(self, request, channels):
        """
        Initialize the channels used for publishing and subscribing messages through the message queue.
        """
        facility = request.path_info.replace(settings.WEBSOCKET_URL, '', 1)

        # initialize publishers
        audience = {
            'users': 'publish-user' in channels and [SELF] or [],
            'groups': 'publish-group' in channels and [SELF] or [],
            'sessions': 'publish-session' in channels and [SELF] or [],
            'broadcast': 'publish-broadcast' in channels,
        }
        self._publishers = set()
        for key in self._get_message_channels(request=request, facility=facility, **audience):
            self._publishers.add(key)

        # initialize subscribers
        audience = {
            'users': 'subscribe-user' in channels and [SELF] or [],
            'groups': 'subscribe-group' in channels and [SELF] or [],
            'sessions': 'subscribe-session' in channels and [SELF] or [],
            'broadcast': 'subscribe-broadcast' in channels,
        }
        self._subscription = self._connection.pubsub()
        for key in self._get_message_channels(request=request, facility=facility, **audience):
            self._subscription.subscribe(key)

    def send_persited_messages(self, websocket):
        """
        This method is called immediately after a websocket is openend by the client, so that
        persisted messages can be sent back to the client upon connection.
        """
        for channel in self._subscription.channels:
            message = self._connection.get(channel)
            if message:
                websocket.send(message)

    def get_file_descriptor(self):
        """
        Returns the file descriptor used for passing to the select call when listening
        on the message queue.
        """
        return self._subscription.connection and self._subscription.connection._sock.fileno()

    def release(self):
        """
        New implementation to free up Redis subscriptions when websockets close. This prevents
        memory sap when Redis Output Buffer and Output Lists build when websockets are abandoned.
        """
        if self._subscription and self._subscription.subscribed:
            self._subscription.unsubscribe()
            self._subscription.reset()
