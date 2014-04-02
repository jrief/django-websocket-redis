.. usage

==========================
Using Websockets for Redis
==========================

**Websocket for Redis** allows uni- and bidirectional communication from the client to the server
and vice versa. Each websocket is identified by the part of the URL which follows the prefix
``/ws/``. Use different uniform locators to distinguish between unrelated communication channels.

.. note:: The prefix ``/ws/`` is specified using the configuration setting ``WEBSOCKET_URL`` and
          can be changed to whatever is appropriate.

Client side
===========
The idea is to let a client subscribe for different channels, so that he only gets notified, when
a certain event happens on a channel he is interested in. Currently there are four such events,
*broadcast notification*, *user notification*, *group notification* and *session notification*.
Additionally, a client may declare on initialization, on which channels he wishes to publish a
message. The latter is not that important for a websocket implementation, because it can be achieved
otherwise, using the well known XMLHttpRequest (Ajax) methods.

Minimal Javascript client:

.. code-block:: javascript

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

Client code using jQuery, being able to reconnect on broken websockets:

.. code-block:: javascript

	(function($) {
	    var ws, deferred, timer, interval = 1000;
	
	    function connect(uri) {
	        try {
	            console.log("Connecting to " + uri);
	            deferred = $.Deferred();
	            ws = new WebSocket(uri);
	            ws.onopen = on_open;
	            ws.onmessage = on_message;
	            ws.onerror = on_error;
	            ws.onclose = on_close;
	            timer = null;
	        } catch (err) {
	            deferred.reject(new Error(err));
	        }
	    }
	
	    function on_open() {
	        console.log("Connected");
	        deferred.resolve();
	    }
	
	    function on_close(evt) {
	        console.log("Connection closed");
	        if (!timer) {
	            timer = setTimeout(function() {
	                connect(ws.url);
	            }, interval);
	        }
	    }
	
	    function on_error(evt) {
	        console.error("Websocket connection is broken!");
	        deferred.reject(new Error(evt));
	    }
	
	    function on_message(evt) {
	        console.log("Received: " + e.data);
	    }
	
	    connect('ws://www.example.com/ws/foobar?subscribe-broadcast');
	}(jQuery));


.. note:: A client wishing to trigger events on the server side, shall use XMLHttpRequests (Ajax),
          as they are much more suitable, rather than messages sent via websockets. The main purpose
          for websockets is to communicate asynchronously from the server to the client.

Server Side
===========
The Django loop is triggered by client HTTP requests, except for special cases such as jobs
triggered by, for instance django-celery_. Intentionally, there is no way to trigger events in the
Django loop through a websocket request. Hence, all of the communication between the Websocket loop
and the Django loop must pass through the message queue.

RedisSubscriber
...............
In the Websocket loop, the message queue is controlled by the class ``RedisSubscriber``, which can
be replaced using the configuration directive ``WS4REDIS_SUBSCRIBER``.

RedisPublisher
..............
In the Django loop, this message queue is controlled by the class ``RedisPublisher``, which can
be accessed by any Django view.

Both, ``RedisSubscriber`` and ``RedisPublisher`` share the same base class ``RedisStore``.

Subscribe to Broadcast Notifications
------------------------------------
This is the simplest form of notification. Every websocket subscribed to a broadcast channel is
notified, when a message is sent to that named Redis channel. Say, the websocket URL is
``ws://www.example.com/ws/foobar?subscribe-broadcast`` and the Django loop wants to publish a
message to all clients listening on the named facility, referred here as ``foobar``.

.. code-block:: python

	from ws4redis.publisher import RedisPublisher
	
	redis_publisher = RedisPublisher(facility='foobar', broadcast=True)
	
	# and somewhere else
	redis_publisher.publish_message('Hello World')

now, the message “Hello World” is received by all clients listening for that broadcast
notification.


Subscribe to User Notification
------------------------------
A websocket initialized with the URL ``ws://www.example.com/ws/foobar?subscribe-user``, will be
notified if that connection belongs to a logged in user and someone publishes a message on for that
user, using the ``RedisPublisher``.

.. code-block:: python

	redis_publisher = RedisPublisher(facility='foobar', users=['john', 'mary'])
	
	# and somewhere else
	redis_publisher.publish_message('Hello World')

now, the message “Hello World” is sent to all clients logged in as ``john`` or ``mary`` and
listening for that kind of notification.

If the message shall be send to the currently logged in user, then you may use the magic item
``SELF``.

.. code-block:: python
	from ws4redis.redis_store import SELF

	redis_publisher = RedisPublisher(facility='foobar', users=[SELF])


Subscribe to Group Notification
-------------------------------
A websocket initialized with the URL ``ws://www.example.com/ws/foobar?subscribe-group``, will be
notified if that connection belongs to a logged in user and someone publishes a message for a
group where this user is member of.

.. code-block:: python

	redis_publisher = RedisPublisher(facility='foobar', groups=['chatters'])
	
	# and somewhere else
	redis_publisher.publish_message('Hello World')

now, the message “Hello World” is sent to all clients logged in as users which are members of the
group ``chatters`` and subscribing to that kind of notification.

In this context the the magic item ``SELF`` refers to all the groups, the current logged in user
belongs to.


Subscribe to Session Notification
---------------------------------
A websocket initialized with the URL ``ws://www.example.com/ws/foobar?subscribe-session``, will be
notified if someone publishes a message for a client owning this session key.

.. code-block:: python

	redis_publisher = RedisPublisher(facility='foobar', sessions=['wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x'])
	
	# and somewhere else
	redis_publisher.publish_message('Hello World')

now, the message “Hello World” is sent to all clients using the session key
``wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x`` and subscribing to that kind of notification.

In this context the the magic item ``SELF`` refers to all clients owning the same session key.


Publish for Broadcast, User, Group and Session
----------------------------------------------
A websocket initialized with the URL ``ws://www.example.com/ws/foobar?publish-broadcast``, 
``ws://www.example.com/ws/foobar?publish-user`` or ``ws://www.example.com/ws/foobar?publish-session``
will publish a message sent through the websocket on the named Redis channel ``broadcast:foobar``,
``user:john:foobar`` and ``session:wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x:foobar`` respectively.
Every listener subscribed to any of the named channels, then will be notified.

This configuration only makes sense, if the messages send by the client using the websocket, shall
not trigger any server side event. A practical use would be to store current the GPS coordinates of
a moving client inside the Redis datastore. Then Django can fetch these coordinates from Redis,
whenever it requires them.

.. code-block:: python

	# if the publisher is required only for fetching messages, use an
	# empty constructor, otherwise reuse an existing redis_publisher
	redis_publisher = RedisPublisher()
	
	# and somewhere else
	facility = 'foobar'
	audience = 'any'
	redis_publisher.fetch_message(request, facility, audience)

The argument ``audience`` must be one of ``broadcast``, ``group``, ``user``, ``session`` or
``any``. The method ``fetch_message`` searches through the Redis datastore to find a persisted
message for that channel. The first found message is returned to the caller. If no matching message
was found, ``None`` is returned.


Persisting messages
-------------------
If a client connects to a Redis channel for the first time, or if he reconnects after a page reload,
he might be interested in the current message, previously published on that channel. If the
configuration settings ``WS4REDIS_EXPIRE`` is set to a positive value, **Websocket for Redis**
persists the current message in its key-value store. This message then is retrieved and sent to
the client, immediately after he connects to the server.

.. note:: By using client code, which automatically reconnects after the websocket closes, one can
          create a setup which is immune against server and client reboots.

.. _django-celery: http://www.celeryproject.org/
