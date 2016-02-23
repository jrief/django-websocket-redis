# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe
from redsocks import settings


def default(request):
    """ Adds additional context variables to the default context. """
    protocol = request.is_secure() and 'wss://' or 'ws://'
    heartbeat_msg = settings.REDSOCKS_HEARTBEAT and '"{0}"'.format(settings.REDSOCKS_HEARTBEAT) or 'null'
    context = {
        'WEBSOCKET_URI': protocol + request.get_host() + settings.WEBSOCKET_URL,
        'REDSOCKS_HEARTBEAT': mark_safe(heartbeat_msg),
    }
    return context
