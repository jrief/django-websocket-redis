# run uWSGI behind NGiNX as:
# uwsgi --virtualenv /path/to/virtualenv --http-socket /var/tmp/web.socket --gevent 10000 --umask 000 --http-websockets --master --workers 2 --module wsgi_websocket
import os
import sys
import gevent.monkey
import gevent.socket
import redis.connection
redis.connection.socket = gevent.socket

sys.path[0:0] = [os.path.abspath('..'), os.path.abspath('../examples')]
os.environ.update(DJANGO_SETTINGS_MODULE='chatserver.settings')

from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
application = uWSGIWebsocketServer()
