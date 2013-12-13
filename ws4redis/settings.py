# -*- coding: utf-8 -*-
from django.conf import settings

REDIS_HOST = getattr(settings, 'WS4REDIS_HOST', 'localhost')

REDIS_PORT = getattr(settings, 'WS4REDIS_PORT', 6379)
