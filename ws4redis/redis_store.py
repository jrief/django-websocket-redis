#-*- coding: utf-8 -*-
from ws4redis import settings


class RedisStore(object):
    """
    Abstract base class to control publishing  and subscription for messages to and from the Redis datastore.
    """
    _expire = settings.WS4REDIS_EXPIRE
    _publishers = set()

    def __init__(self, connection):
        self._connection = connection

    def publish_message(self, message, expire=None):
        """
        Publish a ``message`` on the subscribed channel on the Redis datastore.
        ``expire`` sets the time in seconds, on how long the message shall additionally of being
        published, also be persisted in the Redis datastore. If unset, it defaults to the
        configuration settings ``WS4REDIS_EXPIRE``.
        """
        expire = expire is None and self._expire or expire
        if message:
            for channel in self._publishers:
                self._connection.publish(channel, message)
                if expire > 0:
                    self._connection.set(channel, message, ex=expire)

    def get_prefix(self):
        """
        Returns the string used to prefix entries in the Redis datastore.
        """
        return settings.WS4REDIS_PREFIX and '{0}:'.format(settings.WS4REDIS_PREFIX) or ''

    def _get_message_channels(self, request=None, facility='{facility}', broadcast=False,
                              groups=False, users=False, sessions=False):
        prefix = self.get_prefix()
        channels = []
        if broadcast is True:
            # broadcast message to each subscriber listening on the named facility
            channels.append('{prefix}broadcast:{facility}'.format(prefix=prefix, facility=facility))
        if groups is True and request and request.user.is_authenticated():
            # message is delivered to all groups the currently logged in user belongs to
            channels.extend('{prefix}group:{0}:{facility}'.format(g.name, prefix=prefix, facility=facility)
                            for g in request.user.groups.all())
        elif isinstance(groups, (list, tuple)):
            # message is delivered to all listed groups
            channels.extend('{prefix}group:{0}:{facility}'.format(g, prefix=prefix, facility=facility)
                            for g in groups)
        elif isinstance(groups, basestring):
            # message is delivered to the named group
            channels.append('{prefix}group:{0}:{facility}'.format(groups, prefix=prefix, facility=facility))
        elif not isinstance(groups, bool):
            raise ValueError('Argument `groups` must be a list, a string or a boolean')
        if users is True and request and request.user.is_authenticated():
            # message is delivered to browser instances of the currently logged in user
            channels.append('{prefix}user:{0}:{facility}'.format(request.user.username, prefix=prefix, facility=facility))
        elif isinstance(users, (list, tuple)):
            # message is delivered to all listed users
            channels.extend('{prefix}user:{0}:{facility}'.format(u, prefix=prefix, facility=facility) for u in users)
        elif isinstance(users, basestring):
            # message is delivered to the named user
            channels.append('{prefix}user:{0}:{facility}'.format(users, prefix=prefix, facility=facility))
        elif not isinstance(users, bool):
            raise ValueError('Argument `users` must be a list, a string or a boolean')
        if sessions is True and request and request.session:
            # message is delivered to browser instances owning the current session
            channels.append('{prefix}session:{0}:{facility}'.format(request.session.session_key, prefix=prefix, facility=facility))
        elif isinstance(sessions, (list, tuple)):
            # message is delivered to all browsers instances listed in sessions
            channels.extend('{prefix}session:{0}:{facility}'.format(s, prefix=prefix, facility=facility)
                            for s in sessions)
        elif isinstance(sessions, basestring):
            # message is delivered to the named user
            channels.append('{prefix}session:{0}:{facility}'.format(sessions, prefix=prefix, facility=facility))
        elif not isinstance(sessions, bool):
            raise ValueError('Argument `sessions` must be a boolean')
        return channels
