.. testing

Running Unit Tests
==================

Additional dependencies
-----------------------
To run unit tests, some additional packages have to be installed::

  pip install -r examples/chatserver/tests/requirements.txt

Run the test::

  cd examples && ./manage.py test chatserver

Currently it is only one test, but it covers more than 60% of the code.
