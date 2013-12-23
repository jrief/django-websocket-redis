# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
import redis
from ws4redis import settings as redis_settings


class BaseTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(BaseTemplateView, self).get_context_data(**kwargs)
        context.update(ws_url='ws://{SERVER_NAME}:{SERVER_PORT}/ws/foobar'.format(**self.request.META))
        return context


class BroadcastChatView(BaseTemplateView):
    template_name = 'broadcast_chat.html'


class UserChatView(BaseTemplateView):
    template_name = 'user_chat.html'

    def __init__(self):
        self._connection = redis.StrictRedis(host=redis_settings.REDIS_HOST, port=redis_settings.REDIS_PORT, db=0)

    def get_context_data(self, **kwargs):
        users = User.objects.all()
        context = super(UserChatView, self).get_context_data(**kwargs)
        context.update(users=users)
        return context

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        channel = u'{0}:foobar'.format(request.POST.get('user'))
        self._connection.publish(channel, request.POST.get('message'))
        return HttpResponse('OK')
