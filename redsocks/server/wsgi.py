# -*- coding: utf-8 -*-
"""
Django-Redsox Project 2016
"""
import django
django.setup()

import re, six, sys
from six.moves import http_client
from redis import StrictRedis
from django import http
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.handlers.wsgi import WSGIRequest, logger
from django.utils.encoding import force_str
from importlib import import_module
from redsocks import settings as private_settings
from redsocks.redisstore import RedisMessage
from redsocks.exceptions import WebSocketError, HandshakeError, UpgradeRequiredError


class WSGIWebsocketServer(object):
    
    def __init__(self, redis_connection=None):
        self._subscribers = [(re.compile(p), s) for p,s in private_settings.REDSOCKS_SUBSCRIBERS.items()]
        self._redis_connection = redis_connection and redis_connection or StrictRedis(**private_settings.REDSOCKS_CONNECTION)

    def _find_subscriber(self, request):
        # Lookup subscriber class from facility string
        facility = request.path_info.replace(settings.WEBSOCKET_URL, '', 1)
        for pattern, substr in self._subscribers:
            matches = [pattern.match(facility)]
            if list(filter(None, matches)):
                comps = str(substr).split('.')
                module = import_module('.'.join(comps[:-1]))
                subcls = getattr(module, comps[-1])
                self.possible_channels = subcls.subscription_channels + subcls.publish_channels
                return subcls(self._redis_connection)
        # Found no matching subscribers, raise error
        raise HandshakeError('Unknown facility: %s' % facility)

    def _assert_protocol_requirements(self, environ):
        if environ.get('REQUEST_METHOD') != 'GET':
            raise HandshakeError('HTTP method must be a GET')
        if environ.get('SERVER_PROTOCOL') != 'HTTP/1.1':
            raise HandshakeError('HTTP server protocol must be 1.1')
        if environ.get('HTTP_UPGRADE', '').lower() != 'websocket':
            raise HandshakeError('Client does not wish to upgrade to a websocket')

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
        """ Hijack the main loop and listen on events on the Redis and the Websocket fds. """
        websocket = None
        request = WSGIRequest(environ)
        subscriber = self._find_subscriber(request)
        try:
            self._assert_protocol_requirements(environ)
            subscriber.process_request(request)
            channels, echo_message = self.process_subscriptions(request)
            channels = subscriber.allowed_channels(request, channels)
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
                        print('recvmsg: %s' % recvmsg)
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
                if private_settings.REDSOCKS_HEARTBEAT and not websocket.closed:
                    websocket.send(private_settings.REDSOCKS_HEARTBEAT)
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
                status_text = http_client.responses.get(response.status_code, 'UNKNOWN STATUS CODE')
                status = '{0} {1}'.format(response.status_code, status_text)
                headers = response._headers.values()
                if six.PY3:
                    headers = list(headers)
                start_response(force_str(status), headers)
                logger.info('Finish non-websocket response with status code: {}'.format(response.status_code))
        return response
