# -*- coding: utf-8 -*-
import os
import time
import requests
import six
import django
from django.conf import settings
from django.contrib.auth.models import User
from django.test import LiveServerTestCase
from django.test.client import RequestFactory
from importlib import import_module

from django.core.servers.basehttp import WSGIServer
from websocket import create_connection, WebSocketException
from ws4redis.django_runserver import application
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage, SELF
from ws4redis.tests_helpers import MultiThreadLiveServerTestCase, static_application

from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.keys import Keys

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

    def test_close_connection(self):

        class Counter:
            def __init__(self):
                self.value = 0

        counter = Counter()
        old_handle_error = WSGIServer.handle_error

        def handle_error(self, *args, **kwargs):
            # we need a reference to an object for this to work not a simple variable
            counter.value += 1
            return old_handle_error(self, *args, **kwargs)

        WSGIServer.handle_error = handle_error

        statuses = [1000, 1001, 1002, 1003, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1015, ]
        websocket_url = self.websocket_base_url + u'?subscribe-broadcast&publish-broadcast'
        for status in statuses:
            value_before = counter.value
            ws = create_connection(websocket_url)
            self.assertTrue(ws.connected)
            ws.close(status)
            self.assertFalse(ws.connected)
            self.assertEqual(value_before, counter.value,
                             'Connection error while closing with {}'.format(status))

    def test_protocol_support(self):
        protocol = 'unittestprotocol'
        websocket_url = self.websocket_base_url + u'?subscribe-broadcast&publish-broadcast'
        ws = create_connection(websocket_url, subprotocols=[protocol])
        self.assertTrue(ws.connected)
        self.assertIn('sec-websocket-protocol', ws.headers)
        self.assertEqual(protocol, ws.headers['sec-websocket-protocol'])
        ws.close()
        self.assertFalse(ws.connected)
        ws = create_connection(websocket_url)
        self.assertTrue(ws.connected)
        self.assertNotIn('sec-websocket-protocol', ws.headers)
        ws.close()
        self.assertFalse(ws.connected)

class WebsocketBrowserTests(MultiThreadLiveServerTestCase):
    fixtures = ['data.json']

    @classmethod
    def setUpClass(cls):
        os.environ.update(DJANGO_LIVE_TEST_SERVER_ADDRESS="localhost:8000-8010,8080,9200-9300")
        super(WebsocketBrowserTests, cls).setUpClass()
        cls.server_thread.httpd.set_app(static_application)
        cls.firefox_webdriver = FirefoxWebDriver()
        cls.chrome_webdriver = ChromeWebDriver()
        cls.webdrivers = (cls.firefox_webdriver, cls.chrome_webdriver,)

    @classmethod
    def tearDownClass(cls):
        cls.firefox_webdriver.quit()
        cls.chrome_webdriver.quit()
        super(WebsocketBrowserTests, cls).tearDownClass()

    def test_broadcast_chat(self):
        # We can only use this test witj Django 1.9.
        # This is because of commit https://github.com/django/django/commit/a7901c2e090d720ef
        # which allows us to override part of the httpd server used during the tests, to replace it
        # with one that supports multithreading.

        # We explicitely do not support 1.10 because that override uses private functions, so this
        # hack will need to be reviewed when 1.10 is out.

        if not django.VERSION[0:2] == (1,9):
            self.skipTest('This test is only valid for Django 1.9')

        # Go to the main page, where the broadcast channel is there.
        for webdriver in self.webdrivers:
            webdriver.get(self.live_server_url)

        # From The Tragedy of Hamlet, Prince of Denmark, by William Shakespeare
        messages = (
            (self.firefox_webdriver, 'Who\'s there?',),
            (self.chrome_webdriver, 'Nay, answer me: stand, and unfold yourself.',),
            (self.firefox_webdriver, 'Long live the king!',),
            (self.chrome_webdriver, 'Bernardo?',),
            (self.firefox_webdriver, 'He.',),
            (self.chrome_webdriver, 'You come most carefully upon your hour.',),
            (self.firefox_webdriver, 'Tis now struck twelve; get thee to bed, Francisco.',),
            (self.chrome_webdriver, 'For this relief much thanks: \'tis bitter cold'),
            (self.chrome_webdriver, 'And I am sick at heart.',),
            (self.firefox_webdriver, 'Have you had quiet guard?',),
            (self.chrome_webdriver, 'Not a mouse stirring.',),
            (self.firefox_webdriver, 'Well, good night.',),
            (self.firefox_webdriver, 'If you do meet Horatio and Marcellus,',),
            (self.firefox_webdriver, 'The rivals of my watch, bid them make haste.',),
            (self.chrome_webdriver, 'I think I hear them. Stand, ho!',),
        )

        # Check that we are correctly connected
        time.sleep(5)
        for webdriver in self.webdrivers:
            billboard = webdriver.find_element_by_id('billboard')
            message = 'Hello everybody'
            text = billboard.text
            self.assertEqual(True, message in text)

        # Now we will send the messages
        for webdriver, message in messages:
            text_input = webdriver.find_element_by_id('text_message')
            text_input.send_keys(message)
            text_input.send_keys(Keys.RETURN)
            text_input.clear()
            time.sleep(1)

            # Check that the message is present in BOTH browsers
            for wd in self.webdrivers:
                billboard = wd.find_element_by_id('billboard')
                text = billboard.text
                self.assertEqual(True, message in text)


