.. django-websocket-redis documentation master file

Websockets for Django applications using Redis as message queue
===============================================================

This module implements websockets on top of Django without requiring any additional framework. For
messaging it uses the Redis datastore. In a production environment, it is intended to work under
uWSGI and behind NGiNX. In a development environment, it can be used with ``manage runserver``.

Contents:

.. toctree::

  introduction
  installation
  running
  usage
  testing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

