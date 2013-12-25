#! /usr/bin/env python
# run this test against an instance of uwsgi for websockets
from nose import tools
import threading
from websocket import create_connection


class WebsocketClient(threading.Thread):
    """Simulate a websocket client"""
    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        super(WebsocketClient, self).__init__()

    def run(self):
        ws = create_connection(self.websocket_url)
        assert ws.connected
        result = ws.recv()
        tools.eq_(result, 'Hello, World')
        ws.close()
        tools.eq_(ws.connected, False)


def test_subscribe_publish_broadcast():
    # the sender
    websocket_url = 'ws://localhost:8000/ws/foobar?publish-broadcast'
    ws = create_connection(websocket_url)
    ws.send('Hello, World')

    # the receivers
    websocket_url = 'ws://localhost:8000/ws/foobar?subscribe-broadcast'
    clients = [WebsocketClient(websocket_url) for _ in range(0, 1000)]
    for client in clients:
        client.start()
    for client in clients:
        client.join(5)
    ws.close()
