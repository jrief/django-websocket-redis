# -*- coding: utf-8 -*-
import sys
from redis import StrictRedis
import django
if django.VERSION[:2] >= (1, 7):
    django.setup()
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest, logger, STATUS_CODE_TEXT
from django.core.exceptions import PermissionDenied
from django import http
from django.utils.encoding import force_str
from django.utils.importlib import import_module
from django.utils.functional import SimpleLazyObject
from ws4redis import settings as private_settings
from ws4redis.redis_store import RedisMessage
from ws4redis.exceptions import WebSocketError, HandshakeError, UpgradeRequiredError


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
        agreed_channels = []
        echo_message = False
        for qp in request.GET:
            param = qp.strip().lower()
            if param in self.possible_channels:
                agreed_channels.append(param)
            elif param == 'echo':
                echo_message = True
        return agreed_channels, echo_message

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
            if callable(private_settings.WS4REDIS_PROCESS_REQUEST):
                private_settings.WS4REDIS_PROCESS_REQUEST(request)
            else:
                self.process_request(request)
            channels, echo_message = self.process_subscriptions(request)
            if callable(private_settings.WS4REDIS_ALLOWED_CHANNELS):
                channels = list(private_settings.WS4REDIS_ALLOWED_CHANNELS(request, channels))
            websocket = self.upgrade_websocket(environ, start_response)
            logger.debug('Subscribed to channels: {0}'.format(', '.join(channels)))
            subscriber.set_pubsub_channels(request, channels)
            websocket_fd = websocket.get_file_descriptor()
            listening_fds = [websocket_fd]
            redis_fd = subscriber.get_file_descriptor()
            if redis_fd:
                listening_fds.append(redis_fd)
            subscriber.send_persited_messages(websocket)
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
                if private_settings.WS4REDIS_HEARTBEAT:
                    websocket.send(private_settings.WS4REDIS_HEARTBEAT)
        except WebSocketError as excpt:
            logger.warning('WebSocketError: {}'.format(excpt), exc_info=sys.exc_info())
            response = http.HttpResponse(status=1001, content='Websocket Closed')
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
                status_text = STATUS_CODE_TEXT.get(response.status_code, 'UNKNOWN STATUS CODE')
                status = '{0} {1}'.format(response.status_code, status_text)
                start_response(force_str(status), response._headers.values())
                logger.info('Finish non-websocket response with status code: {}'.format(response.status_code))
        return response
