.. django-websocket-redis documentation master file

Websockets for Django applications using Redis as message queue
===============================================================

This module implements websockets on top of Django without requiring any additional framework. For
messaging it uses the `Redis datastore`_. In a production environment, it is intended to work under
uWSGI_ and behind NGiNX_. In a development environment, it can be used with ``manage runserver``.

Contents:

.. toctree::

  introduction
  installation
  running
  usage
  testing
  motivation

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _NGiNX: http://nginx.com/
.. _uWSGI: http://uwsgi-docs.readthedocs.org/en/latest/WebSockets.html
.. _Redis datastore: http://redis.io/
