# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe
from ws4redis import settings


def default(request):
    """
    Adds additional context variables to the default context.
    """
    protocol = request.is_secure() and 'wss://' or 'ws://'
    heartbeat_msg = settings.WS4REDIS_HEARTBEAT and '"{0}"'.format(settings.WS4REDIS_HEARTBEAT) or 'null'
    context = {
        'WEBSOCKET_URI': protocol + request.get_host() + settings.WEBSOCKET_URL,
        'WS4REDIS_HEARTBEAT': mark_safe(heartbeat_msg),
    }
    return context
