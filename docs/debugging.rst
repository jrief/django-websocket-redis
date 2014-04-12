.. debugging

=========
Debugging
=========

This project adds some extra complexity to Django projects with websocket-redis. This is because now
there are two entry points instead of one. The default **Django** one, based on the WSGI protocol,
which is used to handle the typical HTTP-Request-Response. And the new one **Websocket for Redis**,
based on the HTTP, which handles the websocket part.

Django Loop and Websocket Loop
==============================
In this documentation, I use the terms *Django Loop* and *Websocket Loop* to distinguish these two
entry points. You shall rarely need to access the Websocket Loop, because intentionally there are
no hooks for adding server side logics. The latter must reside inside the Django loop using Redis
as the communication engine between those two.

A reason one might need to debug inside the Websocket loop, is, because the subscriber was
overridden using the configuration setting ``WS4REDIS_SUBSCRIBER``. Therefore, one of the aims of
this project is to facilitate the entry level for debugging. During development, hence the server
is started with ``./manage.py runserver``, this is achieved by hijacking the Django loop. Then the
connection is kept open, until the client closes the Websocket.

If existing workers do not return, Django creates a thread for new incoming requests. This means
that during debugging, each Websocket connection owns its own thread. Such an approach is perfectly
feasible, however it scales badly and therefore should not be used during production.

Query the datastore
===================
Sometimes you might need to know, why some data is bogus or was not sent/received by the client.
The easiest way to do this is to access the Redis datastore.

.. code-block:: bash

	$ redis-cli
	redis 127.0.0.1:6379>

In this command line interface, you can find out about all the data managed by
**Websocket for Redis**. Redis offers many commands_ from which a few are useful here:

.. _commands: http://redis.io/commands

keys
----
.. code-block:: guess

	redis 127.0.0.1:6379> keys *

Gives a list of all keys used in Redis. If a ``WS4REDIS_PREFIX`` is specified in ``settings.py``,
this prefixing string can be used to limit the keys to those used by **Websocket for Redis**.

If, for instance you're interested into all messages available for broadcast, then invoke:

.. code-block:: guess

	redis 127.0.0.1:6379> keys [prefix:]broadcast:*

with the *prefix*, if set.

get
---
.. code-block:: guess

	redis 127.0.0.1:6379> get [prefix:]broadcast:foo

This returns the data available for broadcast for the facility named “foo”.

.. code-block:: guess

	redis 127.0.0.1:6379> get [prefix:]user:john:foo

This returns the data available for user “john” for the facility named “foo”.

.. code-block:: guess

	redis 127.0.0.1:6379> get [prefix:]session:wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x:foo

This returns the data available for the browser owning the session-id
``wnqd0gbw5obpnj50zwh6yaq2yz4o8g9x`` for the facility named “foo”.

subscribe
---------
If **Websocket for Redis** is configured to not cache published data, no data buckets are filled.
This is the case, when the configuration option ``WS4REDIS_EXPIRE`` is set to zero or None. In such
a situation, the Redis commands ``keys`` and ``get`` won't give you any information. But you can
subscribe for listening to a named channel:

.. code-block:: guess

	redis 127.0.0.1:6379> subscribe [prefix:]broadcast:foo

This command blocks until some data is received. It then dumps the received data.

You have to reenter the subscribe command, if you want to listen for further data.
