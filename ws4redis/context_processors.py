# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe
from ws4redis import settings


def default(request):
    """
    Adds additional context variables to the default context.
    """
    host = settings.WEBSOCKET_HOST or request.get_host()
    protocol = request.is_secure() and 'wss://' or 'ws://'
    heartbeat_msg = settings.WS4REDIS_HEARTBEAT and '"{0}"'.format(settings.WS4REDIS_HEARTBEAT) or 'null'
    context = {
        'WEBSOCKET_URI': protocol + host + settings.WEBSOCKET_URL,
        'WS4REDIS_HEARTBEAT': mark_safe(heartbeat_msg),
    }
    return context
