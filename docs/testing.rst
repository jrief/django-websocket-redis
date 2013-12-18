.. testing

Running Unit Tests
==================

Additional dependencies
-----------------------
To run unit tests, some additional packages have to be installed::

  pip install nose django-nose mock websocket-client
  
And in future test::

  mockredispy

The current API does not work yet.

Run the test::

  cd examples && ./manage.py test chatserver
