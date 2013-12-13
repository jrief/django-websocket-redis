django-websocket-redis
======================

Add Websocket support for Django using Redis for message queuing
----------------------------------------------------------------

You can find detailed documentation on [ReadTheDocs](http://django-websocket-redis.readthedocs.org/en/latest/).

Features
--------
* Largely scalable for Django applications with hundreds of open websocket connections.
* Runs in a cooperative concurrency model, thus only one thread/process is simultaneously required
  for all open websockets.
* Full control over the main loop during development, so Django can be started as usual with
  ``./manage.py runserver``.
* No dependencies to any other micro-framework, such as Tornado, Flask or Bottle.
* The only additional requirement is a running instance of Redis.

Build status
------------
.. image:: https://travis-ci.org/jrief/django-websocket-redis.png
   :target: https://travis-ci.org/jrief/django-websocket-redis

License
-------
Copyright (c) 2013 Jacob Rief  
Licensed under the MIT license.

Release History
---------------
* 0.1.0 - initial revision
