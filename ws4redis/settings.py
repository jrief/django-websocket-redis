# -*- coding: utf-8 -*-
from django.conf import settings

REDIS_HOST = getattr(settings, 'REDIS_HOST', 'localhost')

REDIS_PORT = getattr(settings, 'REDIS_PORT', 6379)
