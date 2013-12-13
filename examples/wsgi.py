#! /usr/bin/env uwsgi --virtualenv path/to/virtualenv --http :9090 --gevent 100 --http-websockets --module wsgi
import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from ws4redis.uwsgi_runserver import uWSGIWebsocketServer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatserver.settings')

_django_app = get_wsgi_application()
_websocket_app = uWSGIWebsocketServer()


def application(environ, start_response):
    if environ.get('PATH_INFO').startswith(settings.WEBSOCKET_URL):
        return _websocket_app(environ, start_response)
    return _django_app(environ, start_response)
