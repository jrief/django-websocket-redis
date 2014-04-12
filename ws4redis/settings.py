# -*- coding: utf-8 -*-
from django.conf import settings

WEBSOCKET_URL = getattr(settings, 'WEBSOCKET_URL', '/ws/')

WS4REDIS_CONNECTION = getattr(settings, 'WS4REDIS_CONNECTION', {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
})

"""
A string to prefix elements in the Redis datastore, to avoid naming conflicts with other services.
"""
WS4REDIS_PREFIX = getattr(settings, 'WS4REDIS_PREFIX', None)

"""
The time in seconds, items shall be persisted by the Redis datastore.
"""
WS4REDIS_EXPIRE = getattr(settings, 'WS4REDIS_EXPIRE', 3600)

"""
Replace the subscriber class by a customized version.
"""
WS4REDIS_SUBSCRIBER = getattr(settings, 'WS4REDIS_SUBSCRIBER', 'ws4redis.subscriber.RedisSubscriber')

"""
This set the magic string to recognize heartbeat messages. If set, this message string is ignored
by the server and also shall be ignored on the client.

If set, the server sends at least every 4 seconds a heartbeat message. It is then up to the client
to decide, what to do with these messages.
"""
WS4REDIS_HEARTBEAT = getattr(settings, 'WS4REDIS_HEARTBEAT', None)
