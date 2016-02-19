Django Redsocks
===============

Websockets for Django Using Redis as Message Queue
--------------------------------------------------
This module implements websockets on top of Django without requiring any additional framework. For
messaging it uses the [Redis](http://redis.io/) datastore and in a production environment, it is
intended to work under [uWSGI](http://projects.unbit.it/uwsgi/) and behind [NGiNX](http://nginx.com/)
or [Apache](http://httpd.apache.org/docs/2.4/mod/mod_proxy_wstunnel.html) version 2.4.5 or later.

Project home: https://github.com/mjs7231/django-redsocks

This project is a fork of django-websocket-redis but allows a few additional features. Notably..
* A server-side API to read and act on incoming messages.
* Allows multiple server-side subscribers to websockets.
* Future: Remove the dependance of gevent with the Python3 built-in asyncio.

Features
--------
* Largely scalable for Django applications with many hundreds of open websocket connections.
* Runs a seperate Django main loop in a cooperative concurrency model using [gevent](http://www.gevent.org/),
  thus a single uwsgi process can concurrently handle several hundred websockets simultaneously.
* Updated `django-admin runserver`, allowing full debugging in a development environment.
* No dependency to any other asynchronous event driven frameworks (Tornado, Twisted, Socket.io, NodeJS).
* Normal Django requests communicate with this seperate main loop through Redis.
* Optionally persiting messages, allowing server reboots and client reconnections.

Requirements
------------
* Python 3
* Django 1.8+

License
-------
Copyright &copy; 2015 Jacob Rief, Michael Shepanski.
MIT licensed.
