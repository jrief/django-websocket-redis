# -*- coding: utf-8 -*-
import six
from redsocks import settings

# refers to self as a user or group.
SELF = type('SELF_TYPE', (object,), {})()


class RedisMessage(six.binary_type):
    """ Wraps messages to be sent and received through RedisStore. Behaves like a normal string
        class, but silently discards heartbeats and converts messages received from Redis.
    """
    def __new__(cls, value):
        if six.PY3:
            if isinstance(value, str) and value != settings.REDSOCKS_HEARTBEAT:
                return super(RedisMessage, cls).__new__(cls, value.encode())
            elif isinstance(value, bytes) and value != settings.REDSOCKS_HEARTBEAT.encode():
                return super(RedisMessage, cls).__new__(cls, value)
            elif isinstance(value, list) and len(value) >= 2 and value[0] == b'message':
                return super(RedisMessage, cls).__new__(cls, value[2])
        else:
            if isinstance(value, six.string_types) and value != settings.REDSOCKS_HEARTBEAT:
                return six.binary_type.__new__(cls, value)
            elif isinstance(value, list) and len(value) >= 2 and value[0] == 'message':
                return six.binary_type.__new__(cls, value[2])
        return None


class RedisStore(object):
    """ Abstract base class to control publishing and subscription for messages to and from Redis. """

    def __init__(self, client):
        self.client = client
        self.publishers = set()
        
    @property
    def prefix(self):
        if settings.REDSOCKS_PREFIX:
            return '%s:' % settings.REDSOCKS_PREFIX
        return ''

    def publish_message(self, message, expire=None):
        """ Publish a message on the subscribed channel on the Redis datastore.
            expire sets the time in seconds, on how long the message shall additionally of being
            published, also be persisted in the Redis datastore. If unset, it defaults to the
            configuration settings REDSOCKS_EXPIRE.
        """
        if not isinstance(message, RedisMessage):
            raise ValueError('Message object is not of type RedisMessage')
        expire = expire or settings.REDSOCKS_EXPIRE
        for channel in self.publishers:
            self.client.publish(channel, message)
            if expire > 0:
                self.client.setex(channel, expire, message)

    def _channel(self, facility, broadcast=False, user=None, group=None, session=None):
        """ Return channel name with format {prefix}:{audience}:{facility}. """
        if broadcast is True:
            return '%sbroadcast:%s' % (self.prefix, facility)
        for key, value in [('user',user), ('group',group), ('session',session)]:
            if value is not None:
                return '%s%s:%s' % (self.prefix, key, facility)
        raise Exception('Must specify broadcast, session, user, or group.')

    def _iter_channels(self, facility, request=None, broadcast=False, users=(), groups=(), sessions=()):
        # check audience was passed as a string
        if isinstance(sessions, six.string_types): sessions = (sessions,)
        if isinstance(users, six.string_types): users = (users,)
        if isinstance(groups, six.string_types): groups = (groups,)
        # iterate broadcast, user, group, session channels
        if broadcast is True:
            yield self._channel(facility, broadcast=True)
        for user in self._iter_users(users, request):
            yield self._channel(facility, user=user)
        for group in self._iter_groups(groups, request):
            yield self._channel(facility, group=group)
        for session in self._iter_sessions(sessions, request):
            yield self._channel(facility, session=session)
        
    def _iter_users(self, users, request):
        for user in users:
            if user is SELF and request and request.user and request.user.is_authenticated():
                yield request.user.get_username()
                continue
            yield user
            
    def _iter_groups(self, groups, request):
        for group in groups:
            if group is SELF and request and request.user and request.user.is_authenticated():
                yield request.session.get('redsocks:memberof', [])
                continue
            yield group
            
    def _iter_sessions(self, sessions, request):
        for session in sessions:
            if session is SELF and request:
                yield request.session.session_key
                continue
            yield session
