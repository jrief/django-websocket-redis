# -*- coding: utf-8 -*-
import os
import time
import requests
import six
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.test import LiveServerTestCase, TestCase
from django.test.client import RequestFactory
from django.utils.importlib import import_module
from websocket import create_connection, WebSocketException
from ws4redis.django_runserver import application
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage, SELF


if six.PY3:
    unichr = chr


class WebsocketTests(LiveServerTestCase):
    fixtures = ['data.json']

    @classmethod
    def setUpClass(cls):
        os.environ.update(DJANGO_LIVE_TEST_SERVER_ADDRESS="localhost:8000-8010,8080,9200-9300")
        super(WebsocketTests, cls).setUpClass()
        cls.server_thread.httpd.set_app(application)

    def setUp(self):
        self.facility = u'unittest'
        self.prefix = getattr(settings, 'WS4REDIS_PREFIX', 'ws4redis')
        self.websocket_base_url = self.live_server_url.replace('http:', 'ws:', 1) + u'/ws/' + self.facility
        self.message = RedisMessage(''.join(unichr(c) for c in range(33, 128)))
        self.factory = RequestFactory()
        # SessionStore
        # as used here: http://stackoverflow.com/a/7722483/1913888
        settings.SESSION_ENGINE = 'redis_sessions.session'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

    @classmethod
    def tearDownClass(cls):
        time.sleep(1)

    def test_subscribe_broadcast(self):
        audience = {'broadcast': True}
        publisher = RedisPublisher(facility=self.facility, **audience)
        publisher.publish_message(self.message, 10)
        websocket_url = self.websocket_base_url + u'?subscribe-broadcast'
        ws = create_connection(websocket_url)
        self.assertTrue(ws.connected)
        result = ws.recv()
        if six.PY3:
            self.message = self.message.decode()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_pubsub_broadcast(self):
        websocket_url = self.websocket_base_url + u'?subscribe-broadcast&publish-broadcast'
        ws = create_connection(websocket_url)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        result = ws.recv()
        if six.PY3:
            self.message = self.message.decode()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_publish_broadcast(self):
        websocket_url = self.websocket_base_url + u'?publish-broadcast'
        ws = create_connection(websocket_url)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        ws.close()
        self.assertFalse(ws.connected)
        publisher = RedisPublisher()
        request = self.factory.get('/chat/')
        result = publisher.fetch_message(request, self.facility, 'broadcast')
        self.assertEqual(result, self.message)
        # now access Redis store directly
        self.assertEqual(publisher._connection.get(self.prefix + ':broadcast:' + self.facility), self.message)

    def test_subscribe_user(self):
        logged_in = self.client.login(username='john', password='secret')
        self.assertTrue(logged_in, 'John is not logged in')
        request = self.factory.get('/chat/')
        request.user = User.objects.get(username='mary')
        audience = {'users': ['john', 'mary']}
        publisher = RedisPublisher(request=request, facility=self.facility, **audience)
        publisher.publish_message(self.message, 10)
        websocket_url = self.websocket_base_url + u'?subscribe-user'
        header = ['Cookie: sessionid={0}'.format(self.client.cookies['sessionid'].coded_value)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        result = ws.recv()
        if six.PY3:
            self.message = self.message.decode()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_publish_user(self):
        logged_in = self.client.login(username='john', password='secret')
        self.assertTrue(logged_in, 'John is not logged in')
        websocket_url = self.websocket_base_url + u'?publish-user'
        header = ['Cookie: sessionid={0}'.format(self.client.cookies['sessionid'].coded_value)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        ws.close()
        self.assertFalse(ws.connected)
        publisher = RedisPublisher()
        request = self.factory.get('/chat/')
        request.user = User.objects.get(username='john')
        result = publisher.fetch_message(request, self.facility, 'user')
        self.assertEqual(result, self.message)
        request.user = None
        result = publisher.fetch_message(request, self.facility, 'user')
        self.assertEqual(result, None)

    def test_subscribe_group(self):
        logged_in = self.client.login(username='john', password='secret')
        self.assertTrue(logged_in, 'John is not logged in')
        request = self.factory.get('/chat/')
        request.user = User.objects.get(username='mary')
        audience = {'groups': ['chatters']}
        publisher = RedisPublisher(request=request, facility=self.facility, **audience)
        publisher.publish_message(self.message, 10)
        websocket_url = self.websocket_base_url + u'?subscribe-group'
        header = ['Cookie: sessionid={0}'.format(self.client.cookies['sessionid'].coded_value)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        result = ws.recv()
        if six.PY3:
            self.message = self.message.decode()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_publish_group(self):
        logged_in = self.client.login(username='john', password='secret')
        self.assertTrue(logged_in, 'John is not logged in')
        websocket_url = self.websocket_base_url + u'?publish-group'
        header = ['Cookie: sessionid={0}'.format(self.client.cookies['sessionid'].coded_value)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        ws.close()
        self.assertFalse(ws.connected)
        publisher = RedisPublisher()
        request = self.factory.get('/chat/')
        request.user = User.objects.get(username='mary')
        logged_in = self.client.login(username='mary', password='secret')
        self.assertTrue(logged_in, 'Mary is not logged in')
        request.session = self.client.session
        result = publisher.fetch_message(request, self.facility, 'group')
        self.assertEqual(result, self.message)

    def test_subscribe_session(self):
        logged_in = self.client.login(username='john', password='secret')
        self.assertTrue(logged_in, 'John is not logged in')
        self.assertIsInstance(self.client.session, (dict, type(self.session)), 'Did not receive a session key')
        session_key = self.client.session.session_key
        self.assertGreater(len(session_key), 30, 'Session key is too short')
        request = self.factory.get('/chat/')
        request.session = self.client.session
        audience = {'sessions': [SELF]}
        publisher = RedisPublisher(request=request, facility=self.facility, **audience)
        publisher.publish_message(self.message, 10)
        websocket_url = self.websocket_base_url + u'?subscribe-session'
        header = ['Cookie: sessionid={0}'.format(session_key)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        result = ws.recv()
        if six.PY3:
            self.message = self.message.decode()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_publish_session(self):
        logged_in = self.client.login(username='mary', password='secret')
        self.assertTrue(logged_in, 'Mary is not logged in')
        self.assertIsInstance(self.client.session, (dict, type(self.session)), 'Did not receive a session key')
        session_key = self.client.session.session_key
        self.assertGreater(len(session_key), 30, 'Session key is too short')
        websocket_url = self.websocket_base_url + u'?publish-session'
        header = ['Cookie: sessionid={0}'.format(session_key)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        ws.close()
        self.assertFalse(ws.connected)
        publisher = RedisPublisher()
        request = self.factory.get('/chat/')
        request.session = self.client.session
        result = publisher.fetch_message(request, self.facility, 'session')
        self.assertEqual(result, self.message)

    def test_invalid_request(self):
        websocket_url = self.live_server_url + u'/ws/foobar'
        response = requests.get(websocket_url)
        self.assertEqual(response.status_code, 400)
        content = response.content
        if six.PY3:
            content = content.decode()
        self.assertIn('upgrade to a websocket', content)
        response = requests.post(websocket_url, {})
        self.assertEqual(response.status_code, 400)

    def t_e_s_t_invalid_version(self):
        # does not work: websocket library overrides Sec-WebSocket-Version
        websocket_url = self.websocket_base_url + u'?publish-broadcast'
        header = ['Sec-WebSocket-Version: 6']  # Version 6 is not supported
        ws = create_connection(websocket_url, header=header)
        self.assertFalse(ws.connected)

    def test_defining_multiple_publishers(self):
        pub1 = RedisPublisher(facility=self.facility, broadcast=True)
        self.assertEqual(pub1._publishers, set([self.prefix + ':broadcast:' + self.facility]))
        pub2 = RedisPublisher(facility=self.facility, users=['john'])
        self.assertEqual(pub2._publishers, set([self.prefix + ':user:john:' + self.facility]))

    def test_forbidden_channel(self):
        websocket_url = self.websocket_base_url + u'?subscribe-broadcast&publish-broadcast'
        try:
            create_connection(websocket_url, header=['Deny-Channels: YES'])
            self.fail('Did not reject channels')
        except WebSocketException:
            self.assertTrue(True)
