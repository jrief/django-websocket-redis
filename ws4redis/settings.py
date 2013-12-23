# -*- coding: utf-8 -*-
from django.conf import settings

WS4REDIS_HOST = getattr(settings, 'WS4REDIS_HOST', 'localhost')

WS4REDIS_PORT = getattr(settings, 'WS4REDIS_PORT', 6379)

WS4REDIS_DB = getattr(settings, 'WS4REDIS_DB', 0)

WS4REDIS_PASSWORD = getattr(settings, 'WS4REDIS_PASSWORD', None)

WS4REDIS_EXPIRE = getattr(settings, 'WS4REDIS_EXPIRE', 0)
