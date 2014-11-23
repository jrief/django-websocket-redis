# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from ws4redis.redis_store import RedisMessage
from ws4redis.publisher import RedisPublisher


class BroadcastChatView(TemplateView):
    template_name = 'broadcast_chat.html'

    def get(self, request, *args, **kwargs):
        welcome = RedisMessage('Hello everybody')  # create a welcome message to be sent to everybody
        RedisPublisher(facility='foobar', broadcast=True).publish_message(welcome)
        return super(BroadcastChatView, self).get(request, *args, **kwargs)


class UserChatView(TemplateView):
    template_name = 'user_chat.html'

    def get_context_data(self, **kwargs):
        context = super(UserChatView, self).get_context_data(**kwargs)
        context.update(users=User.objects.all())
        return context

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UserChatView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        redis_publisher = RedisPublisher(facility='foobar', users=[request.POST.get('user')])
        message = RedisMessage(request.POST.get('message'))
        redis_publisher.publish_message(message)
        return HttpResponse('OK')


class GroupChatView(TemplateView):
    template_name = 'group_chat.html'

    def get_context_data(self, **kwargs):
        context = super(GroupChatView, self).get_context_data(**kwargs)
        context.update(groups=Group.objects.all())
        return context

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(GroupChatView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        redis_publisher = RedisPublisher(facility='foobar', groups=[request.POST.get('group')])
        message = RedisMessage(request.POST.get('message'))
        redis_publisher.publish_message(message)
        return HttpResponse('OK')
