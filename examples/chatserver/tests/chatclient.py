# -*- coding: utf-8 -*-
import time
import redis
from django.conf import settings
from django.test import LiveServerTestCase
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

    def test_pending_broadcast(self):
        settings.WS4REDIS_EXPIRE = 10
        self.connection.set('_broadcast_:foobar', self.message)
        websocket_url = self.websocket_base_url + u'/ws/foobar?subscribe-broadcast'
        ws = create_connection(websocket_url)
        self.assertTrue(ws.connected)
        result = ws.recv()
        self.assertEqual(result, self.message)
        ws.close()
        self.assertFalse(ws.connected)

    def test_unified_broadcast(self):
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
