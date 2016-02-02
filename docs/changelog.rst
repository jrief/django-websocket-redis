.. changelog

===============
Release History
===============

0.4.7 develop
-------------


0.4.6
-----
* Added support for the Sec-WebSocket-Protocol header. Thanks to Erwin Junge.
* Fixed bug in unpacking binary websocket protocol.

0.4.5
-----
* created 1 requirements file under ``examples/chatserver/requirements.txt``
* renamed chatclient.py to test_chatclient.py - for django-nose testrunner
* migrated example project to django 1.7
* edited ``docs/testing.rst`` to show new changes for using example project

0.4.4
-----
* Added method ``release()`` to ``RedisSubscriber`` and calling this method each time a Websocket
  closes, for whatever reason. This should avoid some reported memory issues.

0.4.3
-----
* Fixed: **django-websocket-redis** failed to initialize under some circumstances in combination
  with Django-1.7. This only happened for logged in users and threw this exception:
  ``django.core.exceptions.AppRegistryNotReady: Models aren't loaded yet.``
* Added setup on how to run **django-websocket-redis** with uWSGI but without NGiNX.

0.4.2
-----
* Message echoing can be switched “on” and “off” according to the user needs. Before it was “on”
  by default.
* Many changes to get this app compatible with Python3. This is still not finished, since the
  pilfered module ``websocket.py`` is not PY3 compatible yet.
* Added a class ``RedisMessage`` to pass and store the message to and from the websocket.
  Before this was just a string with serialized data.

0.4.1
-----
* Fixed: ``request.user.username`` has been replaced by ``get_username()``.

0.4.0
-----
* Messages can be sent to users being member of one or more Django groups.
* ``RedisPublisher`` and ``RedisSubscriber`` now only accept lists for ``users``, ``groups`` and 
  ``sessions``. This makes the API simpler and more consistent.
* A new magic item ``ws4redis.redis_store.SELF`` has been added to reflect self referencing in
  this list, what before was done through ``users=True`` or ``sessions=True``.
* Added the possibility to receive heartbeats. This lets the client disconnect and attempt to
  reconnect after a number of heartbeats were missed. It prevents silent disconnections.
* Refactored the examples.
* Added reusable JavaScript code for the client.
* Added a context processor to inject some settings from ``ws4redis`` into templates.

0.3.1
-----
* Keys for entries in Redis datastore can be prefixed by an optional string. This may be required
  to avoid namespace clashes.

0.3.0
----- 
* Added possibility to publish and subscribe for Django Groups, additionally to Users and Sesions.
* To ease the communication between Redis and the Django, a new class ``RedisPublisher`` has
  been added as Programming Interface for the Django loop. Before, one had to connect to the Redis
  datastore directly to send messages to the Websoclet loop.
* Renamed configuration setting ``WS4REDIS_STORE`` to ``WS4REDIS_SUBSCRIBER``.

0.2.3
-----
* Fixed: Use flush to discard received PONG message.

0.2.2
-----
* Moved mokey patching for Redis socket into the runner. This sometimes caused errors when
  running in development mode.
* Added timeout to select call. This caused IOerrors when running under uWSGI and the websocket
  was idle.

0.2.1
-----
* Reverted issue #1 and dropped compatibility with Django-1.4 since the response status must
  use force_str.

0.2.0
-----
* Major API changes.
* Use ``WS4REDIS_...`` in Django settings.
* Persist messages, allowing server reboots and reconnecting the client.
* Share the file descriptor for Redis for all open connections.
* Allow to override the subscribe/publish engine.

0.1.2
-----
* Fixed: Can use publish to websocket without subscribing.

0.1.1
-----
* Instead of CLI monkey patching, explicitly patch the redis.connection.socket using
  ``gevent.socket``.

0.1.0
-----
* Initial revision.
