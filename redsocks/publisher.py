#-*- coding: utf-8 -*-
from redis import ConnectionPool, StrictRedis
from redsocks import settings
from redsocks.redisstore import RedisStore

redis_connection_pool = ConnectionPool(**settings.REDSOCKS_CONNECTION)


class RedisPublisher(RedisStore):
    
    def __init__(self, **kwargs):
        """ Initialize the channels for publishing messages through the message queue. """
        client = StrictRedis(connection_pool=redis_connection_pool)
        super(RedisPublisher, self).__init__(client)
        for channel in self._iter_channels(**kwargs):
            self.publishers.add(channel)

    def fetch_message(self, request, facility, audience='any'):
        """ Fetch the first message available for the given facility and audience, if it has been
            persisted in the Redis datastore. The current HTTP request is used to determine to whom
            the message belongs. A unique string is used to identify the bucket's facility. Determines
            the audience to check for the message. Must be one of 'broadcast', 'group', 'user',
            'session' or 'any'. The default is any, which means to check for all possible audiences.
        """
        # create list of channels to look for a message
        channels = []
        if audience in ('session', 'any') and request and request.session:
            channels.append(self._channel(facility, session=request.session.session_key))
        if audience in ('user', 'any') and request and request.user and request.user.is_authenticated():
            channels.append(self._channel(facility, user=request.user.get_username()))
        if audience in ('group', 'any') and request and request.user and request.user.is_authenticated():
            groups = request.session.get('redsocks:memberof', [])
            channels += [self._channel(facility, group=group) for group in groups]
        if audience in ('broadcast', 'any'):
            channels.append(self._channel(facility, broadcast=True))
        # return the first message found
        for channel in channels:
            message = self.store.get(channel)
            if message:
                return message
