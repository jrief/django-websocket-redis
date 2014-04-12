# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns, include
from django.contrib import admin
from views import BroadcastChatView, UserChatView, GroupChatView
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^chat/$', BroadcastChatView.as_view(), name='broadcast_chat'),
    url(r'^userchat/$', UserChatView.as_view(), name='user_chat'),
    url(r'^groupchat/$', GroupChatView.as_view(), name='group_chat'),
    url(r'^admin/', include(admin.site.urls)),
)
