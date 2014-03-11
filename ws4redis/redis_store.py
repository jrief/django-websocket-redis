#-*- coding: utf-8 -*-
from django.conf import settings
from ws4redis import settings as redis_settings


class RedisStore(object):
    """
    Control the messaging from and to the Redis datastore.
    """
    subscription_channels = ['subscribe-session', 'subscribe-user', 'subscribe-broadcast']
    publish_channels = ['publish-session', 'publish-user', 'publish-broadcast']

    def __init__(self, connection, expire=redis_settings.WS4REDIS_EXPIRE):
        self._connection = connection
        self._subscription = None
        self._expire = expire

    def subscribe_channels(self, request, channels):
        """
        Initialize the channels used for subscribing and sending messages.
        """
        def subscribe_for(prefix):
            key = request.path_info.replace(settings.WEBSOCKET_URL, prefix, 1)
            self._subscription.subscribe(key)

        def publish_on(prefix):
            key = request.path_info.replace(settings.WEBSOCKET_URL, prefix, 1)
            self._publishers.add(key)

        self._subscription = self._connection.pubsub()
        self._publishers = set()

        # subscribe to these Redis channels for outgoing messages
        if 'subscribe-session' in channels and request.session:
            subscribe_for('{0}:'.format(request.session.session_key))
        if 'subscribe-user' in channels and request.user:
            subscribe_for('{0}:'.format(request.user))
        if 'subscribe-broadcast' in channels:
            subscribe_for('_broadcast_:')

        # publish incoming messages on these Redis channels
        if 'publish-session' in channels and request.session:
            publish_on('{0}:'.format(request.session.session_key))
        if 'publish-user' in channels and request.user:
            publish_on('{0}:'.format(request.user))
        if 'publish-broadcast' in channels:
            publish_on('_broadcast_:')

    def publish_message(self, message):
        """Publish a message on the subscribed channel on the Redis datastore."""
        if message:
            for channel in self._publishers:
                self._connection.publish(channel, message)
                if self._expire > 0:
                    self._connection.set(channel, message, ex=self._expire)

    def send_persited_messages(self, websocket):
        """
        This method is called immediately after a websocket is openend by the client, so that
        persisted messages can be sent back to the client upon connection.
        """
        for channel in self._subscription.channels:
            message = self._connection.get(channel)
            if message:
                websocket.send(message)

    def parse_response(self):
        """
        Parse a message response sent by the Redis datastore on a subscribed channel.
        """
        return self._subscription.parse_response()

    def get_file_descriptor(self):
        """
        Returns the file descriptor used for passing to the select call when listening
        on the message queue.
        """
        return self._subscription.connection and self._subscription.connection._sock.fileno()
