# -*- coding: utf-8 -*-
import sys

import logging
import six
from six.moves import http_client
from redis import StrictRedis
import django
if django.VERSION[:2] >= (1, 7):
    django.setup()
from django.conf import settings
from django.contrib.auth import get_user
from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import PermissionDenied
from django import http
from django.utils.encoding import force_str
from django.utils.functional import SimpleLazyObject
from ws4redis import settings as private_settings
from ws4redis.redis_store import RedisMessage
from ws4redis.exceptions import WebSocketError, HandshakeError, UpgradeRequiredError

logger = logging.getLogger('django.request')

try:
    # django >= 1.8 && python >= 2.7
    # https://docs.djangoproject.com/en/1.8/releases/1.7/#django-utils-dictconfig-django-utils-importlib
    from importlib import import_module
except ImportError:
    # RemovedInDjango19Warning: django.utils.importlib will be removed in Django 1.9.
    from django.utils.importlib import import_module

try:
    # django >= 1.7
    from django.utils.module_loading import import_string
except ImportError:
    # django >= 1.5
    from django.utils.module_loading import import_by_path as import_string

class WebsocketWSGIServer(object):
    def __init__(self, redis_connection=None):
        """
        redis_connection can be overriden by a mock object.
        """
        comps = str(private_settings.WS4REDIS_SUBSCRIBER).split('.')
        module = import_module('.'.join(comps[:-1]))
        Subscriber = getattr(module, comps[-1])
        self.possible_channels = Subscriber.subscription_channels + Subscriber.publish_channels
        self._redis_connection = redis_connection and redis_connection or StrictRedis(**private_settings.WS4REDIS_CONNECTION)
        self.Subscriber = Subscriber
        self._websockets = set()  # a list of currently active websockets

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
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        if session_key is not None:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore(session_key)
            request.user = SimpleLazyObject(lambda: get_user(request))

    def process_subscriptions(self, request):
        agreed_channels = []
        echo_message = False
        for qp in request.GET:
            param = qp.strip().lower()
            if param in self.possible_channels:
                agreed_channels.append(param)
            elif param == 'echo':
                echo_message = True
        return agreed_channels, echo_message

    @property
    def websockets(self):
        return self._websockets

    def __call__(self, environ, start_response):
        """
        Hijack the main loop from the original thread and listen on events on the Redis
        and the Websocket filedescriptors.
        """
        websocket = None
        subscriber = self.Subscriber(self._redis_connection)
        try:
            self.assure_protocol_requirements(environ)
            request = WSGIRequest(environ)
            if isinstance(private_settings.WS4REDIS_PROCESS_REQUEST, six.string_types):
                import_string(private_settings.WS4REDIS_PROCESS_REQUEST)(request)
            elif callable(private_settings.WS4REDIS_PROCESS_REQUEST):
                private_settings.WS4REDIS_PROCESS_REQUEST(request)
            else:
                self.process_request(request)
            channels, echo_message = self.process_subscriptions(request)
            if callable(private_settings.WS4REDIS_ALLOWED_CHANNELS):
                channels = list(private_settings.WS4REDIS_ALLOWED_CHANNELS(request, channels))
            elif private_settings.WS4REDIS_ALLOWED_CHANNELS is not None:
                try:
                    mod, callback = private_settings.WS4REDIS_ALLOWED_CHANNELS.rsplit('.', 1)
                    callback = getattr(import_module(mod), callback, None)
                    if callable(callback):
                        channels = list(callback(request, channels))
                except AttributeError:
                    pass
            websocket = self.upgrade_websocket(environ, start_response)
            self._websockets.add(websocket)
            logger.debug('Subscribed to channels: {0}'.format(', '.join(channels)))
            subscriber.set_pubsub_channels(request, channels)
            websocket_fd = websocket.get_file_descriptor()
            listening_fds = [websocket_fd]
            redis_fd = subscriber.get_file_descriptor()
            if redis_fd:
                listening_fds.append(redis_fd)
            subscriber.send_persisted_messages(websocket)
            recvmsg = None
            while websocket and not websocket.closed:
                ready = self.select(listening_fds, [], [], 4.0)[0]
                if not ready:
                    # flush empty socket
                    websocket.flush()
                for fd in ready:
                    if fd == websocket_fd:
                        recvmsg = RedisMessage(websocket.receive())
                        if recvmsg:
                            subscriber.publish_message(recvmsg)
                    elif fd == redis_fd:
                        sendmsg = RedisMessage(subscriber.parse_response())
                        if sendmsg and (echo_message or sendmsg != recvmsg):
                            websocket.send(sendmsg)
                    else:
                        logger.error('Invalid file descriptor: {0}'.format(fd))
                # Check again that the websocket is closed before sending the heartbeat,
                # because the websocket can closed previously in the loop.
                if private_settings.WS4REDIS_HEARTBEAT and not websocket.closed:
                    websocket.send(private_settings.WS4REDIS_HEARTBEAT)
                # Remove websocket from _websockets if closed
                if websocket.closed:
                    self._websockets.remove(websocket)
        except WebSocketError as excpt:
            logger.warning('WebSocketError: {}'.format(excpt), exc_info=sys.exc_info())
            response = http.HttpResponse(content='Websocket Closed')
            # bypass status code validation in HttpResponse constructor -- necessary for Django v1.11
            response.status_code = 1001
        except UpgradeRequiredError as excpt:
            logger.info('Websocket upgrade required')
            response = http.HttpResponseBadRequest(status=426, content=excpt)
        except HandshakeError as excpt:
            logger.warning('HandshakeError: {}'.format(excpt), exc_info=sys.exc_info())
            response = http.HttpResponseBadRequest(content=excpt)
        except PermissionDenied as excpt:
            logger.warning('PermissionDenied: {}'.format(excpt), exc_info=sys.exc_info())
            response = http.HttpResponseForbidden(content=excpt)
        except Exception as excpt:
            logger.error('Other Exception: {}'.format(excpt), exc_info=sys.exc_info())
            response = http.HttpResponseServerError(content=excpt)
        else:
            response = http.HttpResponse()
        finally:
            subscriber.release()
            if websocket:
                websocket.close(code=1001, message='Websocket Closed')
            else:
                logger.warning('Starting late response on websocket')
                status_text = http_client.responses.get(response.status_code, 'UNKNOWN STATUS CODE')
                status = '{0} {1}'.format(response.status_code, status_text)
                headers = response._headers.values()
                if six.PY3:
                    headers = list(headers)
                start_response(force_str(status), headers)
                logger.info('Finish non-websocket response with status code: {}'.format(response.status_code))
        return response
