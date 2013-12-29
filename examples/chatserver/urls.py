# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns, include
from django.contrib import admin
from views import BroadcastChatView, UserChatView
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^chat/$', BroadcastChatView.as_view()),
    url(r'^userchat/$', UserChatView.as_view()),
    url(r'^admin/', include(admin.site.urls)),
)
