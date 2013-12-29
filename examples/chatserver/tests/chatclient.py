# -*- coding: utf-8 -*-
import time
import redis
import requests
from django.conf import settings
from django.test import LiveServerTestCase
from django.core.urlresolvers import reverse
from django.contrib.sessions.backends.db import SessionStore
from websocket import create_connection
from ws4redis import settings as redis_settings
from ws4redis.django_runserver import application


class WebsocketTests(LiveServerTestCase):
    fixtures = ['data.json']

    @classmethod
    def setUpClass(cls):
        super(WebsocketTests, cls).setUpClass()
        cls.server_thread.httpd.set_app(application)

    def setUp(self):
        self.websocket_base_url = self.live_server_url.replace('http:', 'ws:', 1)
        self.message = ''.join(unichr(c) for c in range(33, 128))
        self.connection = redis.StrictRedis(**redis_settings.WS4REDIS_CONNECTION)

    @classmethod
    def tearDownClass(cls):
        time.sleep(1)

    def test_subscribe_broadcast(self):
        settings.WS4REDIS_EXPIRE = 10
        self.connection.set('_broadcast_:foobar', self.message)
        websocket_url = self.websocket_base_url + u'/ws/foobar?subscribe-broadcast'
        ws = create_connection(websocket_url)
        self.assertTrue(ws.connected)
        result = ws.recv()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_pubsub_broadcast(self):
        settings.WS4REDIS_EXPIRE = 0
        websocket_url = self.websocket_base_url + u'/ws/foobar?subscribe-broadcast&publish-broadcast'
        ws = create_connection(websocket_url)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        result = ws.recv()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_publish_broadcast(self):
        settings.WS4REDIS_EXPIRE = 10
        websocket_url = self.websocket_base_url + u'/ws/foobar?publish-broadcast'
        ws = create_connection(websocket_url)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        ws.close()
        self.assertFalse(ws.connected)
        result = self.connection.get('_broadcast_:foobar')
        self.assertEqual(result, self.message)

    def test_subscribe_user(self):
        logged_in = self.client.login(username='admin', password='secret')
        self.assertTrue(logged_in, 'User is not logged in')
        settings.WS4REDIS_EXPIRE = 10
        self.connection.set('admin:foobar', self.message)
        websocket_url = self.websocket_base_url + u'/ws/foobar?subscribe-user'
        header = ['Cookie: sessionid={0}'.format(self.client.cookies['sessionid'].coded_value)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        result = ws.recv()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_publish_user(self):
        logged_in = self.client.login(username='admin', password='secret')
        self.assertTrue(logged_in, 'User is not logged in')
        settings.WS4REDIS_EXPIRE = 10
        websocket_url = self.websocket_base_url + u'/ws/foobar?publish-user'
        header = ['Cookie: sessionid={0}'.format(self.client.cookies['sessionid'].coded_value)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        ws.close()
        self.assertFalse(ws.connected)
        result = self.connection.get('admin:foobar')
        self.assertEqual(result, self.message)

    def test_subscribe_session(self):
        response = self.client.get(reverse('admin:index'))
        self.assertIsInstance(response.client.session, SessionStore, 'Did not receive a sessionid')
        session_key = response.client.session.session_key
        self.assertGreater(len(session_key), 30, 'Session key is too short')
        settings.WS4REDIS_EXPIRE = 10
        self.connection.set('{0}:foobar'.format(session_key), self.message)
        websocket_url = self.websocket_base_url + u'/ws/foobar?subscribe-session'
        header = ['Cookie: sessionid={0}'.format(session_key)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        result = ws.recv()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_publish_session(self):
        response = self.client.get(reverse('admin:index'))
        self.assertIsInstance(response.client.session, SessionStore, 'Did not receive a sessionid')
        session_key = response.client.session.session_key
        self.assertGreater(len(session_key), 30, 'Session key is too short')
        settings.WS4REDIS_EXPIRE = 10
        websocket_url = self.websocket_base_url + u'/ws/foobar?publish-session'
        header = ['Cookie: sessionid={0}'.format(session_key)]
        ws = create_connection(websocket_url, header=header)
        self.assertTrue(ws.connected)
        ws.send(self.message)
        ws.close()
        self.assertFalse(ws.connected)
        result = self.connection.get('{0}:foobar'.format(session_key))
        self.assertEqual(result, self.message)

    def test_invalid_request(self):
        websocket_url = self.live_server_url + u'/ws/foobar'
        response = requests.get(websocket_url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('upgrade to a websocket', response.content)
        response = requests.post(websocket_url, {})
        self.assertEqual(response.status_code, 400)

    def t_e_s_t_invalid_version(self):
        # does not work: websocket library overrides Sec-WebSocket-Version
        websocket_url = self.websocket_base_url + u'/ws/foobar?publish-broadcast'
        header = ['Sec-WebSocket-Version: 6']  # Version 6 is not supported
        ws = create_connection(websocket_url, header=header)
        self.assertFalse(ws.connected)
