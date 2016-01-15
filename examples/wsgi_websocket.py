# entry point for the websocket loop
import gevent.monkey
gevent.monkey.patch_thread()

from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
application = uWSGIWebsocketServer()
