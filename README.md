django-websocket-redis
======================

Project home: https://github.com/jrief/django-websocket-redis

Detailed documentation on: [ReadTheDocs](http://django-websocket-redis.readthedocs.org/en/latest/).

Websockets for Django using Redis as message queue
--------------------------------------------------
This module implements websockets on top of Django without requiring any additional framework. For
messaging it uses the [Redis](http://redis.io/) datastore and in a production environment, it is
intended to work under [uWSGI](http://projects.unbit.it/uwsgi/) and behind [NGiNX](http://nginx.com/).

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
Copyright (c) 2014 Jacob Rief
Licensed under the MIT license.
