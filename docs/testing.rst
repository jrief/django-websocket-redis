.. testing

Testing Websockets for Redis
============================

Simple Chat servers
-------------------
In the ``examples`` directory, there are two demo chat servers. To start them, first initialize
the SQLite database::

  ./manage.py syncdb
  Creating tables ...
  ...
  Would you like to create one now? (yes/no): yes
  Username (leave blank to use 'admin'): admin
  ...

and then start the server::

  ./manage.py runserver

Now, point a browser onto http://localhost:8000/admin/, login and add additional users with enabled
staff status to the database.

With http://localhost:8000/userchat/ you then can send messages to specific users, provided they
are logged in. To log in as another user, use the admin interface.

Simple Broadcasting
...................
On http://localhost:8000/chat/ there is a chat server, which simply broadcasts messages to all
browsers accessing this same URL.


Running Unit Tests
------------------
To run the unit tests, a few additional packages have to be installed::

  pip install -r examples/chatserver/tests/requirements.txt

Run the tests::

  cd examples && ./manage.py test chatserver --settings=chatserver.test_settings

Currently there is only one test, but it covers more than 60% of the code.
