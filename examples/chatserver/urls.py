# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns
from django.shortcuts import render


urlpatterns = patterns('',
     url(r'^chat/$', lambda request: render(request, 'chat.html',
         { 'ws_url': 'ws://localhost:{SERVER_PORT}/ws/foobar'.format(**request.META) })),
)
