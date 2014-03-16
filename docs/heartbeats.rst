.. heartbeats

========================================
Sending and receiving heartbeat messages
========================================

The websocket protocol implements so called PING/PONG messages to keep websockets alive, even behind
proxies, firewalls and load-balancers. The server sends a PING message to the client through the
websocket, which then replies with PONG. Unfortunately this keep alive strategy does not work in all
configurations. Sometimes the client times out and looses the websocket connection, but does not
recognizing this, because there was no event for closing the socket.

Since 