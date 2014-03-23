.. django-websocket-redis documentation master file

===============================================================
Websockets for Django applications using Redis as message queue
===============================================================

This module implements websockets on top of Django without requiring any additional framework. For
messaging it uses the `Redis datastore`_. In a production environment, it is intended to work under
uWSGI_ and behind NGiNX_. In a development environment, it can be used with ``manage runserver``.

Project's home
==============
Check for the latest release of this project on `Github`_.

Please report bugs or ask questions using the `Issue Tracker`_.

Contents
========
.. toctree::

  introduction
  installation
  running
  usage
  heartbeats
  api
  testing
  debugging
  changelog
  credits

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _NGiNX: http://nginx.com/
.. _uWSGI: http://uwsgi-docs.readthedocs.org/en/latest/WebSockets.html
.. _Redis datastore: http://redis.io/
.. _Github: https://github.com/jrief/django-websocket-redis
.. _Issue Tracker: https://github.com/jrief/django-websocket-redis/issues
