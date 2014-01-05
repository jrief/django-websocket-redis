#! /usr/bin/env python
# run this test against an instance of uwsgi for websockets
from nose import tools
import gevent
from gevent import monkey
monkey.patch_socket()
from websocket import create_connection


def test_simple():
    def listen_on_websocket(closure):
        ws = create_connection(closure['websocket_url'])
        assert ws.connected
        result = ws.recv()
        print '+',
        tools.eq_(result, 'Hello, World')
        ws.close()
        tools.eq_(ws.connected, False)
        closure['counter'] -= 1

    # the sender
    websocket_url = 'ws://localhost:8000/ws/foobar?publish-broadcast'
    ws = create_connection(websocket_url)
    assert ws.connected
    ws.send('Hello, World')

    # the receivers
    closure = {
        'websocket_url': 'ws://localhost:8000/ws/foobar?subscribe-broadcast',
        'counter': 1000,
    }
    clients = [gevent.spawn(listen_on_websocket, closure) for _ in range(0, closure['counter'])]
    gevent.joinall(clients, timeout=5)
    ws.close()
    tools.eq_(ws.connected, False)
    tools.eq_(closure['counter'], 0)
