# -*- coding: utf-8 -*-
from django.conf import settings


def ws4redis(request):
    """
    Adds additional context variables to the default context.
    """
    context = {
        'WEBSOCKET_URL': settings.WEBSOCKET_URL,
        'WS4REDIS_HEARTBEAT': settings.WS4REDIS_HEARTBEAT,
    }
    return context
