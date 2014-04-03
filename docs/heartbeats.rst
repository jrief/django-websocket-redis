.. heartbeats

========================================
Sending and receiving heartbeat messages
========================================

The Websocket protocol implements so called PING/PONG messages to keep Websockets alive, even behind
proxies, firewalls and load-balancers. The server sends a PING message to the client through the
Websocket, which then replies with PONG. If the client does not reply, the server closes
the connection.

The client part
---------------
Unfortunately, the Websocket protocol does not provide a similar method for the client, to find out
if it is still connected to the server. This can happen, if the connection simply disappears without
further notification. In order to have the client recognize this, some Javascript code has to be
added to the client code responsible for the Websocket:

.. code-block:: javascript

	var ws = new WebSocket('ws://www.example.com/ws/foobar?subscribe-broadcast');
	var heartbeat_msg = '--heartbeat--', heartbeat_interval = null, missed_heartbeats = 0;
	
	function on_open() {
	    // ...
	    // other code which has to be executed after the client
	    // connected successfully through the websocket
	    // ...
	    if (heartbeat_interval === null) {
	        missed_heartbeats = 0;
	        heartbeat_interval = setInterval(function() {
	            try {
	                missed_heartbeats++;
	                if (missed_heartbeats >= 3)
	                    throw new Error("Too many missed heartbeats.");
	                ws.send(heartbeat_msg);
	            } catch(e) {
	                clearInterval(heartbeat_interval);
	                heartbeat_interval = null;
	                console.warn("Closing connection. Reason: " + e.message);
	                ws.close();
	            }
	        }, 5000);
	    }
	}

The heartbeat message, here ``--heartbeat--`` can be any magic string which does not interfere with
your remaining logic. The best way to achieve this, is to check for that magic string inside the
receive function, just before further processing the message:

.. code-block:: javascript

	function on_message(evt) {
	    if (evt.data === heartbeat_msg) {
	        // reset the counter for missed heartbeats
	        missed_heartbeats = 0;
	        return;
	    }
	    // ...
	    // code to further process the received message
	    // ...
	}

The server part
---------------
The main loop of the Websocket server is idle for a maximum of 4 seconds, even if there is nothing
to do. After that time interval has elapsed, this loop optionally sends a magic string to the
client. This can be configured using the special setting:

.. code-block:: python

	WS4REDIS_HEARTBEAT = '--heartbeat--'

The purpose of this setting is twofold. During processing, the server ignores incoming messages
containing this magic string. Additionally the Websocket server sends a message with that magic
string to the client, about every four seconds. The above client code awaits these messages, at
least every five seconds, and if too many were not received, it closes the connection and tries
to reestablish it.

By default the setting ``WS4REDIS_HEARTBEAT`` is ``None``, which means that heartbeat messages are
neither expected nor sent.
