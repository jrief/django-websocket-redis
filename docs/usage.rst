.. usage

Using Websockets for Redis
==========================

**Websocket for Redis** allows uni- and bidirectional communication from the client to the server
and vice versa. Each websocket is identified by the part of the URL which follows the prefix
``/ws/``. Use different uniform locators to distinguish between unrelated communication channels.

.. note:: The prefix ``/ws/`` is specified using the configuration setting ``WEBSOCKET_URL``.

The idea is to let a client subscribe for different channels, so that he only gets notified, when
a certain event happens on that channel. Currently there are three such events, broadcast
notification, user notification and session notification. Additionally a client may declare on
initialization, on which channels he wishes to publish a message. The latter is not that important
for a websocket implementation, because this can be achieved using the well known XMLHttpRequest
(Ajax) protocols.

Typical client JavaScript code may look like::

	var ws = new WebSocket('ws://www.example.com/ws/foobar?subscribe-broadcast&publish-broadcast');
	ws.onopen = function() {
		console.log("websocket connected");
	};
	ws.onmessage = function(e) {
		console.log("Received: " + e.data);
	};
	ws.onerror = function(e) {
		console.error(e);
	};
	ws.onclose = function(e) {
		console.log("connection closed");
	}
	function send_message(msg) {
		ws.send(msg);
	}


Subscribe to Broadcast Notification
-----------------------------------
This is the simplest form of notification. Every websocket subscribed to a broadcast channel is
notified, when a notification is sent to that named Redis channel. Say, the websocket URL is
``ws://www.example.com/ws/foobar&subscribe-broadcast`` and in Django someone publishes a message
to Redis using::

  conn = redis.StrictRedis()
  conn.publish('_broadcast_:foobar', 'Hello World')

then, the message “Hello World” is received by all clients listening for that broadcast
notification.

Subscribe to User Notification
------------------------------
A websocket initialized with the URL ``ws://www.example.com/ws/foobar&subscribe-user``, will be
notified if someone publishes a message on a named Redis channel using::

  conn = redis.StrictRedis()
  conn.publish('johndoe:foobar', 'Hello World')

then the message “Hello World” is sent to all clients logged in as ``johndoe`` and listening for
that user notification.

Subscribe to Session Notification
---------------------------------
A websocket initialized with the URL ``ws://www.example.com/ws/foobar&subscribe-session``, will be
notified if someone publishes a message on a named Redis channel using::

  conn = redis.StrictRedis()
  conn.publish('wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x:foobar', 'Hello World')

then the message “Hello World” is sent to all clients using the Session-Id 
``wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x`` and listening for that user notification.

Publish for Broadcast, User and Session
---------------------------------------
A websocket initialized with the URL ``ws://www.example.com/ws/foobar&publish-broadcast``, will
publish a message sent through the websocket on the named Redis channels ``_broadcast_:foobar``,
``johndoe:foobar`` and ``wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x:foobar`` respectively. Every listener
subscribed to any of those named channels, then will be notified.
