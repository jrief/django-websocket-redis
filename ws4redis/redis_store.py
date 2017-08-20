# -*- coding: utf-8 -*-
import six
import warnings
from ws4redis import settings
from ws4redis._compat import is_authenticated


"""
A type instance to handle the special case, when a request shall refer to itself, or as a user,
or as a group.
"""
SELF = type('SELF_TYPE', (object,), {})()


def _wrap_users(users, request):
    """
    Returns a list with the given list of users and/or the currently logged in user, if the list
    contains the magic item SELF.
    """
    result = set()
    for u in users:
        if u is SELF and is_authenticated(request):
            result.add(request.user.get_username())
        else:
            result.add(u)
    return result


def _wrap_groups(groups, request):
    """
    Returns a list of groups for the given list of groups and/or the current logged in user, if
    the list contains the magic item SELF.
    Note that this method bypasses Django's own group resolution, which requires a database query
    and thus is unsuitable for coroutines.
    Therefore the membership is takes from the session store, which is filled by a signal handler,
    while the users logs in.
    """
    result = set()
    for g in groups:
        if g is SELF and is_authenticated(request):
            result.update(request.session.get('ws4redis:memberof', []))
        else:
            result.add(g)
    return result


def _wrap_sessions(sessions, request):
    """
    Returns a list of session keys for the given lists of sessions and/or the session key of the
    current logged in user, if the list contains the magic item SELF.
    """
    result = set()
    for s in sessions:
        if s is SELF and request:
            result.add(request.session.session_key)
        else:
            result.add(s)
    return result


class RedisMessage(six.binary_type):
    """
    A class wrapping messages to be send and received through RedisStore. This class behaves like
    a normal string class, but silently discards heartbeats and converts messages received from
    Redis.
    """
    def __new__(cls, value):
        if six.PY3:
            if isinstance(value, str):
                if value != settings.WS4REDIS_HEARTBEAT:
                    value = value.encode()
                    return super(RedisMessage, cls).__new__(cls, value)
            elif isinstance(value, (bytes, bytearray)):
                if settings.WS4REDIS_HEARTBEAT is None or value != settings.WS4REDIS_HEARTBEAT.encode():
                    return super(RedisMessage, cls).__new__(cls, value)
            elif isinstance(value, list):
                if len(value) >= 2 and value[0] == b'message':
                    return super(RedisMessage, cls).__new__(cls, value[2])
        else:
            if isinstance(value, (six.string_types, bytearray)):
                if value != settings.WS4REDIS_HEARTBEAT:
                    return six.binary_type.__new__(cls, value)
            elif isinstance(value, list):
                if len(value) >= 2 and value[0] == 'message':
                    return six.binary_type.__new__(cls, value[2])
        return None


class RedisStore(object):
    """
    Abstract base class to control publishing and subscription for messages to and from the Redis
    datastore.
    """
    _expire = settings.WS4REDIS_EXPIRE

    def __init__(self, connection):
        self._connection = connection
        self._publishers = set()

    def publish_message(self, message, expire=None):
        """
        Publish a ``message`` on the subscribed channel on the Redis datastore.
        ``expire`` sets the time in seconds, on how long the message shall additionally of being
        published, also be persisted in the Redis datastore. If unset, it defaults to the
        configuration settings ``WS4REDIS_EXPIRE``.
        """
        if expire is None:
            expire = self._expire
        if not isinstance(message, RedisMessage):
            raise ValueError('message object is not of type RedisMessage')
        for channel in self._publishers:
            self._connection.publish(channel, message)
            if expire > 0:
                self._connection.setex(channel, expire, message)

    @staticmethod
    def get_prefix():
        return settings.WS4REDIS_PREFIX and '{0}:'.format(settings.WS4REDIS_PREFIX) or ''

    def _get_message_channels(self, request=None, facility='{facility}', broadcast=False,
                              groups=(), users=(), sessions=()):
        prefix = self.get_prefix()
        channels = []
        if broadcast is True:
            # broadcast message to each subscriber listening on the named facility
            channels.append('{prefix}broadcast:{facility}'.format(prefix=prefix, facility=facility))

        # handle group messaging
        if isinstance(groups, (list, tuple)):
            # message is delivered to all listed groups
            channels.extend('{prefix}group:{0}:{facility}'.format(g, prefix=prefix, facility=facility)
                            for g in _wrap_groups(groups, request))
        elif groups is True and is_authenticated(request):
            # message is delivered to all groups the currently logged in user belongs to
            warnings.warn('Wrap groups=True into a list or tuple using SELF', DeprecationWarning)
            channels.extend('{prefix}group:{0}:{facility}'.format(g, prefix=prefix, facility=facility)
                            for g in request.session.get('ws4redis:memberof', []))
        elif isinstance(groups, basestring):
            # message is delivered to the named group
            warnings.warn('Wrap a single group into a list or tuple', DeprecationWarning)
            channels.append('{prefix}group:{0}:{facility}'.format(groups, prefix=prefix, facility=facility))
        elif not isinstance(groups, bool):
            raise ValueError('Argument `groups` must be a list or tuple')

        # handle user messaging
        if isinstance(users, (list, tuple)):
            # message is delivered to all listed users
            channels.extend('{prefix}user:{0}:{facility}'.format(u, prefix=prefix, facility=facility)
                            for u in _wrap_users(users, request))
        elif users is True and is_authenticated(request):
            # message is delivered to browser instances of the currently logged in user
            warnings.warn('Wrap users=True into a list or tuple using SELF', DeprecationWarning)
            channels.append('{prefix}user:{0}:{facility}'.format(request.user.get_username(), prefix=prefix, facility=facility))
        elif isinstance(users, basestring):
            # message is delivered to the named user
            warnings.warn('Wrap a single user into a list or tuple', DeprecationWarning)
            channels.append('{prefix}user:{0}:{facility}'.format(users, prefix=prefix, facility=facility))
        elif not isinstance(users, bool):
            raise ValueError('Argument `users` must be a list or tuple')

        # handle session messaging
        if isinstance(sessions, (list, tuple)):
            # message is delivered to all browsers instances listed in sessions
            channels.extend('{prefix}session:{0}:{facility}'.format(s, prefix=prefix, facility=facility)
                            for s in _wrap_sessions(sessions, request))
        elif sessions is True and request and request.session:
            # message is delivered to browser instances owning the current session
            warnings.warn('Wrap a single session key into a list or tuple using SELF', DeprecationWarning)
            channels.append('{prefix}session:{0}:{facility}'.format(request.session.session_key, prefix=prefix, facility=facility))
        elif isinstance(sessions, basestring):
            # message is delivered to the named user
            warnings.warn('Wrap a single session key into a list or tuple', DeprecationWarning)
            channels.append('{prefix}session:{0}:{facility}'.format(sessions, prefix=prefix, facility=facility))
        elif not isinstance(sessions, bool):
            raise ValueError('Argument `sessions` must be a list or tuple')
        return channels
