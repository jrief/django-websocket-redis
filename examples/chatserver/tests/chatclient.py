# -*- coding: utf-8 -*-
import time
from django.test import LiveServerTestCase
from websocket import create_connection
from ws4redis.django_runserver import application


class WebsocketTests(LiveServerTestCase):
    fixtures = ['data.json']

    @classmethod
    def setUpClass(cls):
        super(WebsocketTests, cls).setUpClass()
        cls.server_thread.httpd.set_app(application)

    def setUp(self):
        self.websocket_url = self.live_server_url.replace('http:', 'ws:', 1) + u'/ws/foobar?subscribe-broadcast&publish-broadcast'

    @classmethod
    def tearDownClass(cls):
        time.sleep(1)

    def test_echo_broadcast(self):
        ws = create_connection(self.websocket_url)
        self.assertTrue(ws.connected)
        ws.send('Hello, World')
        result = ws.recv()
        self.assertEqual(result, 'Hello, World')
        ws.close()
        self.assertFalse(ws.connected)
