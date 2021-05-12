# -*- coding: utf-8 -*-
from django import template

try:
    from django.core.urlresolvers import reverse
except ImportError as e:
    from django.urls import reverse

register = template.Library()


@register.simple_tag
def active(request, url):
    if request.path.startswith(reverse(url)):
        return 'active'
    return ''
