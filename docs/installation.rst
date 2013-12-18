.. _installation_and_configuration:

Installation and Configuration
==============================

Installation
------------
If not already done, install **Redis**, using your operation systems tools such as ``aptitude``,
``yum``, ``port`` or install `Redis from source`_.

Start the Redis service on your host. It normally listens on port 6379.

Install **Django Websocket for Redis**. The latest stable release can be found on PyPI::

  pip install django-websocket-redis

or the newest development version from github::

  pip install -e git+https://github.com/jrief/django-websocket-redis#egg=django-websocket-redis

Dependencies
------------
* Django_ >=1.5
* `Python client for Redis`_
* uWSGI_ >= 1.9.22
* gevent_ >=1.0
* greenlet_ >=0.4.1

Configuration
-------------
Add ``"ws4redis"`` to your project's ``INSTALLED_APPS`` setting::

  INSTALLED_APPS = (
      ...
      'ws4redis',
      ...
  )

Specify the URL that distinguishes websocket connections from normal requests::

  WEBSOCKET_URL = '/ws/'

If Redis runs on a host other than localhost or a port other than 6379, override the default
settings::

  REDIS_HOST = 'host.example.com'
  REDIS_PORT = 6379

This setting is required during development and ignored in production. It overrides Django's
internal main loop and adds a URL dispatcher in front of the request handler::

  WSGI_APPLICATION = 'ws4redis.django_runserver.application'

Check your Installation
-----------------------
With **Websockets for Redis** your Django application has immediate access to code written for
websockets. Make sure, that Redis is running, then change into the ``examples`` directory and 
start a sample chat server::

  ./manage.py syncdb
  ... database tables are created
  ... answer the questions
  ./manage.py runserver

Point your browser onto http://localhost:8000/chat/ , you should see a simple chat server. Enter
a message and send it to the server. It should be echoed immediately into the billboard.

Point a second browser onto the same URL. Now each browser should echo the message entered into
input field.

In the examples directory, there are two chat server implementations, which run out of the box and
can be used as a starting point.

Unit Testing
------------
To run unit tests, some additional dependencies must be resolved:

* nose
* django-nose
* mock
* websocket-client
* mockredispy (currently not used)

Run the test::

  cd examples && ./manage.py test chatserver

.. _Redis from source: http://redis.io/download
.. _github: https://github.com/jrief/django-websocket-redis
.. _Django: http://djangoproject.com/
.. _Python client for Redis: https://pypi.python.org/pypi/redis/
.. _gevent: https://pypi.python.org/pypi/gevent
.. _greenlet: https://pypi.python.org/pypi/greenlet
