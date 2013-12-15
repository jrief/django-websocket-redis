# -*- coding: utf-8 -*-
from django.test import TestCase
#from django.test.client import RequestFactory
from django.test.client import Client
from mock import patch
from mockredis import mock_strict_redis_client



class TestCase1(TestCase):
    @patch('redis.StrictRedis', mock_strict_redis_client)
    def setUp(self):
        pass

    def test_1(self):
        client = Client()
        ws_http_headers = { 'HTTP_UPGRADE': 'upgrade' }
        # , extra=ws_http_headers
        request = client.request(ws_http_headers)
        #print response.content
        self.assertTrue(True)
