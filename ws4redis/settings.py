# -*- coding: utf-8 -*-
from django.conf import settings

WEBSOCKET_URL = getattr(settings, 'WEBSOCKET_URL', '/ws/')

WS4REDIS_CONNECTION = getattr(settings, 'WS4REDIS_CONNECTION', {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
})

WS4REDIS_EXPIRE = getattr(settings, 'WS4REDIS_EXPIRE', 3600)

WS4REDIS_SUBSCRIBER = getattr(settings, 'WS4REDIS_SUBSCRIBER', 'ws4redis.subscriber.RedisSubscriber')
