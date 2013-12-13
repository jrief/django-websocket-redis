# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns
from django.shortcuts import render_to_response


urlpatterns = patterns('',
    url(r'^chat/$', lambda r: render_to_response('chat.html', { 'ws_url': 'ws://localhost:8000/ws/foobar' })),
)
