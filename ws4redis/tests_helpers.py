from django.core.servers.basehttp import WSGIServer
from django.test.testcases import LiveServerThread, QuietWSGIRequestHandler, LiveServerTestCase, _StaticFilesHandler
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.utils.six.moves import socketserver
from ws4redis.django_runserver import _websocket_url, _websocket_app, _django_app

def static_application(environ, start_response):
    """An alternative WSGI App that can be used with websockets, because it redirects between
    websocket and other requests. It is meant to be used with LiveServerTestcase."""
    if _websocket_url and environ.get('PATH_INFO').startswith(_websocket_url):
        return _websocket_app(environ, start_response)
    return _StaticFilesHandler(_django_app)(environ, start_response)


class MultiThreadLiveServerThread(LiveServerThread):
    """A LiveServerThread that supports simultaneous connections. Note that the function we
    override is only present since Django 1.9, so it won't work with previous versions."""

    def _create_server(self, port):
        httpd_cls = type('WSGIServer', (socketserver.ThreadingMixIn, WSGIServer), {'daemon_threads': True})
        return httpd_cls((self.host, port), QuietWSGIRequestHandler)

class MultiThreadLiveServerTestCase(LiveServerTestCase):
    """ This class extends the LiveServerTestCase with a webserver thread that supports
    multithreading. Note that the function we override is only present since Django 1.9, so it
    won't work with previous versions."""

    @classmethod
    def _create_server_thread(cls, host, possible_ports, connections_override):
        return MultiThreadLiveServerThread(
            host,
            possible_ports,
            cls.static_handler,
            connections_override=connections_override,
        )

class MultiThreadStaticLiveServerTestCase(MultiThreadLiveServerTestCase):
    """Extends MultiThreadLiveServerTestCase to transparently overlay at test
    execution-time the assets provided by the staticfiles app finders."""

    static_handler = StaticFilesHandler
