#-*- coding: utf-8 -*-
import sys
from redis import StrictRedis
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest, logger, STATUS_CODE_TEXT
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from django.utils.encoding import force_str
from django.utils.importlib import import_module
from django.utils.functional import SimpleLazyObject
from ws4redis import settings as redis_settings
from ws4redis.exceptions import WebSocketError, HandshakeError, UpgradeRequiredError
from ws4redis import signals


class WebsocketWSGIServer(object):
    def __init__(self, redis_connection=None):
        """
        redis_connection can be overriden by a mock object.
        """
        comps = str(redis_settings.WS4REDIS_SUBSCRIBER).split('.')
        module = import_module('.'.join(comps[:-1]))
        Subscriber = getattr(module, comps[-1])
        self.allowed_channels = Subscriber.subscription_channels + Subscriber.publish_channels
        self._redis_connection = redis_connection and redis_connection or StrictRedis(**redis_settings.WS4REDIS_CONNECTION)
        self.Subscriber = Subscriber

    def assure_protocol_requirements(self, environ):
        if environ.get('REQUEST_METHOD') != 'GET':
            raise HandshakeError('HTTP method must be a GET')

        if environ.get('SERVER_PROTOCOL') != 'HTTP/1.1':
            raise HandshakeError('HTTP server protocol must be 1.1')

        if environ.get('HTTP_UPGRADE', '').lower() != 'websocket':
            raise HandshakeError('Client does not wish to upgrade to a websocket')

    def process_request(self, request):
        request.session = None
        request.user = None
        if 'django.contrib.sessions.middleware.SessionMiddleware' in settings.MIDDLEWARE_CLASSES:
            engine = import_module(settings.SESSION_ENGINE)
            session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
            if session_key:
                request.session = engine.SessionStore(session_key)
                if 'django.contrib.auth.middleware.AuthenticationMiddleware' in settings.MIDDLEWARE_CLASSES:
                    from django.contrib.auth import get_user
                    request.user = SimpleLazyObject(lambda: get_user(request))

    def process_subscriptions(self, request):
        requested_channels = [p.strip().lower() for p in request.GET]
        agreed_channels = [p for p in requested_channels if p in self.allowed_channels]
        return agreed_channels

    def __call__(self, environ, start_response):
        """ Hijack the main loop from the original thread and listen on events on Redis and Websockets"""
        websocket = None
        subscriber = self.Subscriber(self._redis_connection)
        try:
            self.assure_protocol_requirements(environ)
            request = WSGIRequest(environ)
            self.process_request(request)
            channels = self.process_subscriptions(request)
            websocket = self.upgrade_websocket(environ, start_response)
            logger.debug('Subscribed to channels: {0}'.format(', '.join(channels)))
            subscriber.set_pubsub_channels(request, channels)
            websocket_fd = websocket.get_file_descriptor()
            listening_fds = [websocket_fd]
            redis_fd = subscriber.get_file_descriptor()
            if redis_fd:
                listening_fds.append(redis_fd)
            subscriber.send_persited_messages(websocket)
            while websocket and not websocket.closed:
                ready = self.select(listening_fds, [], [], 4.0)[0]
                if not ready:
                    # flush empty socket
                    websocket.flush()
                for fd in ready:
                    if fd == websocket_fd:
                        message = websocket.receive()
                        if message != redis_settings.WS4REDIS_HEARTBEAT:
                            subscriber.publish_message(message)
                    elif fd == redis_fd:
                        response = subscriber.parse_response()
                        if response[0] == 'message':
                            message = response[2]
                            websocket.send(message)
                    else:
                        logger.error('Invalid file descriptor: {0}'.format(fd))
                if redis_settings.WS4REDIS_HEARTBEAT:
                    websocket.send(redis_settings.WS4REDIS_HEARTBEAT)
        except WebSocketError, excpt:
            logger.warning('WebSocketError: ', exc_info=sys.exc_info())
            response = HttpResponse(status=1001, content='Websocket Closed')
        except UpgradeRequiredError, excpt:
            logger.info('Websocket upgrade required')
            response = HttpResponseBadRequest(status=426, content=excpt)
        except HandshakeError, excpt:
            logger.warning('HandshakeError: ', exc_info=sys.exc_info())
            response = HttpResponseBadRequest(content=excpt)
        except Exception, excpt:
            logger.error('Other Exception: ', exc_info=sys.exc_info())
            response = HttpResponseServerError(content=excpt)
        else:
            response = HttpResponse()
        if websocket:
            websocket.close(code=1001, message='Websocket Closed')
        if hasattr(start_response, 'im_self') and not start_response.im_self.headers_sent:
            logger.warning('Staring late response on websocket')
            status_text = STATUS_CODE_TEXT.get(response.status_code, 'UNKNOWN STATUS CODE')
            status = '{0} {1}'.format(response.status_code, status_text)
            start_response(force_str(status), response._headers.values())
        logger.info('Finish long living response with status code: '.format(response.status_code))
        return response
