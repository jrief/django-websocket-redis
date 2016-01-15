.. testing

============================
Testing Websockets for Redis
============================

A simple Chat server
====================
In the ``examples`` directory, there are two demo chat servers. To start them, first initialize
the SQLite database

.. code-block:: bash

	# create python2 virtualenv
	virtualenv - p /path/to/python2 /path/to/virtualenv

	# activate virtualenv
	source /path/to/virtualenv/bin/activate

	# Make sure you're in the examples/ directory
	cd examples/

	# install pip requirements
	pip install -r requirements.txt

	# Django 1.7+
	# Load test data
	./manage.py migrate
	./manage.py loaddata chatserver/fixtures/data.json

and then start the server

.. code-block:: bash

	# start Redis Server from a different shell prompt
	# (or follow quickstart instructions http://redis.io/topics/quickstart)
	redis-server

	# start Django
	./manage.py runserver

Point a browser onto http://localhost:8000/admin/, login as the 'admin' user using the password
'secret' and add additional users. Enable their staff status, so that they can use the admin
interface to log into the testing application.

With http://localhost:8000/chat/ you can send messages to specific users, provided they are
logged in. To log in as another user, use Django's admin interface.

Simple Broadcasting
-------------------
On http://localhost:8000/chat/ there is a chat server, which simply broadcasts messages to all
browsers accessing this same URL.

Testing uWSGI
-------------
Before configuring NGiNX to run in front of two instances of uWSGI, it is recommended to run
uWSGI as a stand alone server for testing purpose. The entry point of this server makes the
distinction between normal HTTP and Websocket requests. In directory ``examples``, start uwsgi as

.. code-block:: bash

	uwsgi --virtualenv /path/to/virtualenvs --http :9090 --gevent 100 --http-websockets --module wsgi

Both chat server tests from above should run in this configuration.

Running Unit Tests
==================

.. code-block:: bash

	./manage.py test chatserver --settings=chatserver.tests.settings

Currently it is not possible to simulate more than one client at a time. Django's built in
LiveServerTestCase_ can not handle more than one simultaneous open connection, and thus more
sophisticated tests with more than one active Websockets are not possible.


Running Stress Tests
====================
To run stress tests, change into directory ``stress-tests``. Since stress tests shall check the
performance in a real environment, the server and the testing client must be started independently.

First start the server, as you would in productive environments.

.. code-block:: bash

	# Open a new shell and activate your virtualenv in it
	source /path/to/virtualenv/bin/activate

	# Install the uwsgi package
	pip install uwsgi

	# Then start the uwsgi server
	uwsgi --http :8000 --gevent 1000 --http-websockets --master --workers 2 --module wsgi_websocket

then go back to the other shell (also with the virtualenv activated) and start one of the testing
clients, using the nose_ framework

.. code-block:: bash

	nosetests test_uwsgi_gevent.py

(this test, on my MacBook, requires about 1.5 seconds)

or start a similar test using real threads instead of greenlets

.. code-block:: bash

	nosetests test_uwsgi_threads.py

(this test, on my MacBook, requires about 2.5 seconds)

Both clients subscribe to 1000 concurrent Websockets. Then a message is published from another
Websocket. If all the clients receive that message, the test is considered as successful. Both
perform the same test, but ``test_uwsgi_gevent.py`` uses greenlet_'s for each client to simulate,
whereas ``test_uwsgi_threads.py`` uses `Python thread`_'s.

If these tests do not work in your environment, check your file descriptors limitations. Use the
shell command ``ulimit -n`` and adopt it to these requirements. Alternatively reduce the number of
concurrent clients in the tests.

.. _LiveServerTestCase: https://docs.djangoproject.com/en/1.6/topics/testing/overview/#liveservertestcase
.. _nose: http://nose.readthedocs.org/en/latest/
.. _greenlet: http://greenlet.readthedocs.org/en/latest/
.. _Python thread: http://docs.python.org/2/library/threading.html
