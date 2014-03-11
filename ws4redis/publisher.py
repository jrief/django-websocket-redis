#-*- coding: utf-8 -*-
from redis import ConnectionPool, StrictRedis
from ws4redis import settings
from ws4redis.redis_store import RedisStore

redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)


class RedisPublisher(RedisStore):
    def __init__(self, **kwargs):
        """
        Initialize the channels for publishing messages through the message queue.
        """
        connection = StrictRedis(connection_pool=redis_connection_pool)
        super(RedisPublisher, self).__init__(connection)
        for key in self._get_message_channels(**kwargs):
            self._publishers.add(key)

    def fetch_message(self, request, facility, audience='any'):
        """
        Fetch the first message available for the given `facility` and `audience`, if it has been
        persisted in the Redis datastore.
        @param request: The current HTTP request used to determine to whom the message belongs.
        @param facility: A unique string to identify the bucket.
        @param audience: Determines the audience to check for the message. Can be of `broadcast`,
            `group`, `user`, `session` or `any`. `any` means to check for all audiences.
        """
        channels = []
        if audience in ('session', 'any',):
            if request.session:
                channels.append('session:{0}:{facility}'.format(request.session.session_key, facility=facility))
        if audience in ('user', 'any',):
            if request.user.is_authenticated():
                channels.append('user:{0}:{facility}'.format(request.user.username, facility=facility))
        if audience in ('group', 'any',):
            if request.user.is_authenticated():
                groups = request.user.groups.all()
                channels.extend('group:{0}:{facility}'.format(g.name, facility=facility) for g in groups)
        if audience in ('broadcast', 'any',):
            channels.append('broadcast:{facility}'.format(facility=facility))
        for channel in channels:
            message = self._connection.get(channel)
            if message:
                return message
