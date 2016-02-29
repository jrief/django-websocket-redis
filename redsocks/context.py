# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe
from redsocks import settings


def default(request):
    protocol = 'wss://' if request.is_secure() else 'ws://'
    heartbeat = '"%s"' % settings.REDSOCKS_HEARTBEAT if settings.REDSOCKS_HEARTBEAT else 'null'
    return {
        'WEBSOCKET_PROTOCOL': protocol,
        'WEBSOCKET_URI': '%s%s%s' % (protocol, request.get_host(), settings.WEBSOCKET_URL),
        'REDSOCKS_HEARTBEAT': mark_safe(heartbeat),
    }
