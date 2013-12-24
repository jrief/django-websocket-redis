# -*- coding: utf-8 -*-
from django.conf import settings

WS4REDIS_CONNECTION = getattr(settings, 'WS4REDIS_CONNECTION', {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
})

WS4REDIS_EXPIRE = getattr(settings, 'WS4REDIS_EXPIRE', 3600)

WS4REDIS_STORE = getattr(settings, 'WS4REDIS_STORE', 'ws4redis.store.RedisStore')
