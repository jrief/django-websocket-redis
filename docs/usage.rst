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

A minimal client in pure JavaScript
-----------------------------------

.. code-block:: javascript

	var ws = new WebSocket('ws://www.example.com/ws/foobar?subscribe-broadcast&publish-broadcast&echo');
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

Client JavaScript depending on jQuery
-------------------------------------
When using jQuery, clients can reconnect on broken Websockets. Additionally the client awaits for
heartbeat messages and reconnects if too many of them were missed.

Include the client code in your template:

.. code-block:: html

	<script type="text/javascript" src="{{ STATIC_URL }}js/ws4redis.js"></script>

and access the Websocket code:

.. code-block:: javascript

	jQuery(document).ready(function($) {
	    var ws4redis = WS4Redis({
	        uri: '{{ WEBSOCKET_URI }}foobar?subscribe-broadcast&publish-broadcast&echo',
	        receive_message: receiveMessage,
	        connected: on_connected,
	        heartbeat_msg: {{ WS4REDIS_HEARTBEAT }}
	    });

	    // attach this function to an event handler on your site
	    function sendMessage() {
	        ws4redis.send_message('A message');
	    }
	    
	    function on_connected() {
	        ws4redis.send_message('Hello');
	    }

	    // receive a message though the websocket from the server
	    function receiveMessage(msg) {
	        alert('Message from Websocket: ' + msg);
	    }
	});

This example shows how to configure a Websocket for bidirectional communication.

.. note:: A client wishing to trigger events on the server side, shall use XMLHttpRequests (Ajax),
          as they are much more suitable, rather than messages sent via Websockets. The main purpose
          for Websockets is to communicate asynchronously from the server to the client.


Server Side
===========
The Django loop is triggered by client HTTP requests, except for special cases such as jobs
triggered by, for instance django-celery_. Intentionally, there is no way to trigger events in the
Django loop through a Websocket request. Hence, all of the communication between the Websocket loop
and the Django loop must pass through the message queue.

.. _django-celery: http://www.celeryproject.org/

RedisSubscriber
---------------
In the Websocket loop, the message queue is controlled by the class ``RedisSubscriber``, which can
be replaced using the configuration directive ``WS4REDIS_SUBSCRIBER``.

RedisPublisher
--------------
In the Django loop, this message queue is controlled by the class ``RedisPublisher``, which can
be accessed by any Django view.

Both, ``RedisSubscriber`` and ``RedisPublisher`` share the same base class ``RedisStore``.

Subscribe to Broadcast Notifications
------------------------------------
This is the simplest form of notification. Every Websocket subscribed to a broadcast channel is
notified, when a message is sent to that named Redis channel. Say, the Websocket URL is
``ws://www.example.com/ws/foobar?subscribe-broadcast`` and the Django loop wants to publish a
message to all clients listening on the named facility, referred here as ``foobar``.

.. code-block:: python

	from ws4redis.publisher import RedisPublisher
	from ws4redis.redis_store import RedisMessage

	redis_publisher = RedisPublisher(facility='foobar', broadcast=True)
	message = RedisMessage('Hello World')
	# and somewhere else
	redis_publisher.publish_message(message)

now, the message “Hello World” is received by all clients listening for that broadcast
notification.

Subscribe to User Notification
------------------------------
A Websocket initialized with the URL ``ws://www.example.com/ws/foobar?subscribe-user``, will be
notified if that connection belongs to a logged in user and someone publishes a message on for that
user, using the ``RedisPublisher``.

.. code-block:: python

	redis_publisher = RedisPublisher(facility='foobar', users=['john', 'mary'])
	message = RedisMessage('Hello World')
	# and somewhere else
	redis_publisher.publish_message(message)

now, the message “Hello World” is sent to all clients logged in as ``john`` or ``mary`` and
listening for that kind of notification.

If the message shall be send to the currently logged in user, then you may use the magic item
``SELF``.

.. code-block:: python

	from ws4redis.redis_store import SELF

	redis_publisher = RedisPublisher(facility='foobar', users=[SELF], request=request)

Subscribe to Group Notification
-------------------------------
A Websocket initialized with the URL ``ws://www.example.com/ws/foobar?subscribe-group``, will be
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

.. note::  This feature uses a signal handler in the Django loop, which determines the groups a user
           belongs to. This list of groups then is persisted inside a session variable to avoid
           having the Websocket loop to access the database.

Subscribe to Session Notification
---------------------------------
A Websocket initialized with the URL ``ws://www.example.com/ws/foobar?subscribe-session``, will be
notified if someone publishes a message for a client owning this session key.

.. code-block:: python

	redis_publisher = RedisPublisher(facility='foobar', sessions=['wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x'])
	message = RedisMessage('Hello World')

	# and somewhere else
	redis_publisher.publish_message(message)

now, the message “Hello World” is sent to all clients using the session key
``wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x`` and subscribing to that kind of notification.

In this context the the magic item ``SELF`` refers to all clients owning the same session key.

Publish for Broadcast, User, Group and Session
----------------------------------------------
A Websocket initialized with the URL ``ws://www.example.com/ws/foobar?publish-broadcast``,
``ws://www.example.com/ws/foobar?publish-user`` or ``ws://www.example.com/ws/foobar?publish-session``
will publish a message sent through the Websocket on the named Redis channel ``broadcast:foobar``,
``user:john:foobar`` and ``session:wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x:foobar`` respectively.
Every listener subscribed to any of the named channels, then will be notified.

This configuration only makes sense, if the messages send by the client using the Websocket, shall
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

Message echoing
---------------
Some kind of applications require to just hold a state object on the server-side, which is a copy
of a corresponding JavaScript object on the client. These applications do not require message
echoing. Here an incoming message is only dispatched to the subscribed websockets, if the this
message contains a different content. This is the default setting.

Other applications such as chats or games, must be informed on each message published
on the message queue, regardless of its content. These applications require message echoing.
Here an incoming message is always dispatched to the subscribed websockets. To activate message
echoing, simply append the parameter ``&echo`` to the URL used for connecting to the websocket.

Persisting messages
-------------------
If a client connects to a Redis channel for the first time, or if he reconnects after a page reload,
he might be interested in the current message, previously published on that channel. If the
configuration settings ``WS4REDIS_EXPIRE`` is set to a positive value, **Websocket for Redis**
persists the current message in its key-value store. This message then is retrieved and sent to
the client, immediately after he connects to the server.

.. note:: By using client code, which automatically reconnects after the Websocket closes, one can
          create a setup which is immune against server and client reboots.

.. _SafetyConsiderations:

Safety considerations
---------------------
The default setting of **Websocket for Redis** is to allow each client to subscribe and to publish
on every possible channel. This normally is not what you want. Therefore **Websocket for Redis**
allows to restrict the channels for subscription and publishing to your application needs. This is
done by a callback function, which is called right after the initialization of the Websocket.
This function shall be used to restrict the subscription/publishing channels for the current client.

Example:

.. code-block:: python

	def get_allowed_channels(request, channels):
	    return set(channels).intersection(['subscribe-broadcast', 'subscribe-group'])

This function restricts the allowed channels to ``subscribe-broadcast`` and ``subscribe-group``
only. All other attempts to subscribe or to publish on other channels will be silently discarded.

Disallow non authenticated users to subscribe or to publish on the Websocket:

.. code-block:: python

	from django.core.exceptions import PermissionDenied

	def get_allowed_channels(request, channels):
	    if not request.user.is_authenticated():
	        raise PermissionDenied('Not allowed to subscribe nor to publish on the Websocket!')

When using this callback function, Websockets opened by a non-authenticated users, will get a
**403 - Response Forbidden** error.

To enable this function in your application, use the configuration directive
``WS4REDIS_ALLOWED_CHANNELS``.

.. note:: This function must not perform any blocking requests, such as accessing the database!
