.. changelog

===============
Release History
===============

0.3.1
-----
* Keys for entries in Redis datastore can be prefixed by an optional string. This may be required
  to avoid namespace clashes.

0.3.0
----- 
* Added possibility to publish and subscribe for Django Groups, additionally to Users and Sesions.
* To ease the communication between Redis and the Django, a new class ``RedisPublisher`` has
  been added as Programming Interface for the Django loop. Before, one had to connect to Redis
  directly.
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
