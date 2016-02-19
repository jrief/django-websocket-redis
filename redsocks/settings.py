# -*- coding: utf-8 -*-
from django.conf import settings

WEBSOCKET_URL = getattr(settings, 'WEBSOCKET_URL', '/ws/')

REDSOCKS_CONNECTION = getattr(settings, 'REDSOCKS_CONNECTION', {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
})

"""
A string to prefix elements in the Redis datastore, to avoid naming conflicts with other services.
"""
REDSOCKS_PREFIX = getattr(settings, 'REDSOCKS_PREFIX', None)

"""
The time in seconds, items shall be persisted by the Redis datastore.
"""
REDSOCKS_EXPIRE = getattr(settings, 'REDSOCKS_EXPIRE', 3600)

"""
Replace the subscriber class by a customized version.
"""
REDSOCKS_SUBSCRIBER = getattr(settings, 'REDSOCKS_SUBSCRIBER', 'redsocks.subscriber.RedisSubscriber')
REDSOCKS_SUBSCRIBERS = getattr(settings, 'REDSOCKS_SUBSCRIBERS', {'.*':'redsocks.subscriber.RedisSubscriber'})

"""
This set the magic string to recognize heartbeat messages. If set, this message string is ignored
by the server and also shall be ignored on the client.

If REDSOCKS_HEARTBEAT is not None, the server sends at least every 4 seconds a heartbeat message.
It is then up to the client to decide, what to do with these messages.
"""
REDSOCKS_HEARTBEAT = getattr(settings, 'REDSOCKS_HEARTBEAT', None)


"""
If set, this callback function is called instead of the default process_request function in WebsocketWSGIServer.
This function can be used to enforce custom authentication flow. i.e. JWT
"""
REDSOCKS_PROCESS_REQUEST = getattr(settings, 'REDSOCKS_PROCESS_REQUEST', None)
