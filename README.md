django-websocket-redis
======================

Websockets for Django using Redis as message queue
--------------------------------------------------

This module implements websockets on top of Django without requiring any additional framework. For
messaging it uses the [Redis](http://redis.io/) datastore and in a production environment, it is
intended to work under [uWSGI](http://projects.unbit.it/uwsgi/) and behind [NGiNX](http://nginx.com/).

You can find detailed documentation on [ReadTheDocs](http://django-websocket-redis.readthedocs.org/en/latest/).

Features
--------
* Largely scalable for Django applications with hundreds of open websocket connections.
* Runs in a cooperative concurrency model using [gevent](http://www.gevent.org/), thus only one
  thread/process is simultaneously required to control **all** open websockets.
* Full control over the main loop during development, so **Django** can be started as usual with
  ``./manage.py runserver``.
* No dependency to any other asynchronous event driven framework, such as Tornado, Twisted or
  Node.js.
* Optionally persiting messages, allowing server reboots and client reconnections.
* The only additional requirement is a running instance of **Redis**, which by the way is a good
  replacement for memcached.

Build status
------------
[![Build Status](https://travis-ci.org/jrief/django-websocket-redis.png?branch=master)](https://travis-ci.org/jrief/django-websocket-redis)

Questions
---------
Please use the issue tracker to ask questions.

License
-------
Copyright (c) 2013 Jacob Rief  
Licensed under the MIT license.

Release History
---------------
* 0.2.0 - Major API change
 * Use WS4REDIS_... in Django settings
 * Persist messages, allowing server reboots and reconnecting the client
 * Share the file descriptor for Redis for all open connections
 * Allow to override the subscribe/publish engine
* 0.1.2 - fixed: Can use publish to websocket without subscribing
* 0.1.1 - instead of CLI monkey patching, explicitly patch the redis.connection.socket using gevent.socket
* 0.1.0 - initial revision

[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/jrief/django-websocket-redis/trend.png)](https://bitdeli.com/free "Bitdeli Badge")
