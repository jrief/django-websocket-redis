# -*- coding: utf-8 -*-
from django.conf import settings

WEBSOCKET_URL = getattr(settings, 'WEBSOCKET_URL', '/ws/')
REDSOCKS_CONNECTION = getattr(settings, 'REDSOCKS_CONNECTION', {
    'host':'localhost', 'port':6379, 'db':0, 'password':None,
})
REDSOCKS_HEARTBEAT = getattr(settings, 'REDSOCKS_HEARTBEAT', None)
REDSOCKS_PREFIX = getattr(settings, 'REDSOCKS_PREFIX', None)
REDSOCKS_EXPIRE = getattr(settings, 'REDSOCKS_EXPIRE', 3600)
REDSOCKS_SUBSCRIBERS = getattr(settings, 'REDSOCKS_SUBSCRIBERS', {
    '.*':'redsocks.subscriber.RedisSubscriber'
})
