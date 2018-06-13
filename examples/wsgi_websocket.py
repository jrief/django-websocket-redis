# Django with WebSockets for Redis behind NGiNX using uWSGI
# (for sites requiring scalability)
# 
# Note: this is entry point for the websocket loop
#
# uwsgi --virtualenv /path/to/virtualenv --http-socket /path/to/web.socket --gevent 1000 --http-websockets --workers=2 --master --module wsgi_websocket
# 
# See: http://django-websocket-redis.readthedocs.io/en/latest/running.html#django-with-websockets-for-redis-behind-nginx-using-uwsgi

import gevent.monkey
gevent.monkey.patch_thread()

from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
application = uWSGIWebsocketServer()

import os
import gevent.socket
import redis.connection
redis.connection.socket = gevent.socket
os.environ.update(DJANGO_SETTINGS_MODULE='chatserver.settings')
from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
application = uWSGIWebsocketServer()
