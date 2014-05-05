# -*- coding: utf-8 -*-
from django.core.exceptions import PermissionDenied


def denied_channels(request, channels):
    if request.META.get('HTTP_DENY_CHANNELS') == 'YES':
        raise PermissionDenied('No channels are allowed')
    return channels
