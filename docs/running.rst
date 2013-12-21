.. running

Running Websocket for Redis
===========================

**Websocket for Redis** is a library which runs side by side with Django. It has its own separate
main loop, which does nothing other than keeping the websocket alive and dispatching requests
from **Redis** to the configured websockets and vice versa.

Running Django with websockets for Redis in development mode
------------------------------------------------------------
With **Websockets for Redis** your Django application has immediate access to code written for
websockets. Make sure, that Redis is up and accepting connections::

  $ redis-cli ping
  PONG

Then start the Django development server::

  ./manage.py runserver

As usual, this command shall only be used for development.

The ``runserver`` command is a monkey patched version of the original Django main loop and works
similar to it. If an incoming request is of type WSGI, everything works as usual. However, if the
patched handler detects an incoming request wishing to open a websocket, then the Django main
loop is hijacked by **ws4redis**. This separate loop then waits until ``select`` notifies that some
data is available for further processing, or by the websocket itself, or by the Redis message queue.
This hijacked main loop finishes when the websocket is closed or when an error occurs.

.. note:: In development, one thread is created for each open websocket.

Opened websocket connections exchange so called Ping/Pong messages. They keep the connections open,
even if there is no payload to be sent. In development mode, the main loop does not send
these stay alive packages, because normally there is no proxy or firewall between the server and the
client which could drop the connection. This could be easily implemented, though.

Running Django with websockets for Redis as a stand alone uWSGI server
----------------------------------------------------------------------
In this configuration the uWSGI server owns the main loop. To distinguish websockets from normals
requests, modify the Python starter module ``wsgi.py`` to::

  import os
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
  from django.conf import settings
  from django.core.wsgi import get_wsgi_application
  from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
  
  _django_app = get_wsgi_application()
  _websocket_app = uWSGIWebsocketServer()
  
  def application(environ, start_response):
      if environ.get('PATH_INFO').startswith(settings.WEBSOCKET_URL):
          return _websocket_app(environ, start_response)
      return _django_app(environ, start_response)

Run uWSGI as stand alone server with::

  uwsgi --virtualenv /path/to/virtualenv --http :80 --gevent 100 --http-websockets --module wsgi

This will answer, both Django and websocket requests on port 80 using HTTP. Here the modified
``application`` dispatches incoming requests depending on the URL on either a Django handler or
into the websocket's main loop.

This configuration works for testing uWSGI and low traffic sites. Since uWSGI then runs in one
thread/process, blocking calls such as accessing the database, would also block all other HTTP
requests. Adding ``--gevent-monkey-patch`` to the command line may help here, but Postgres for
instance requires to monkey patch its blocking calls with **gevent** using the psycogreen_ library.
Moreover, only one CPU core is then used and static files must be handled by another webserver.

Running Django with websockets for Redis behind NGiNX using uWSGI
-----------------------------------------------------------------
This is the most scalable solution. Here two instances of a uWSGI server are spawned, one to handle
normal HTTP requests for Django and one to handle websocket requests. Look at this diagram:

|websocket4redis|

The webserver undertakes the task of dispatching normal requests to one uWSGI instance and websocket
requests to another one. The responsible configuration section for an NGiNX webserver shall look
like::

  location / {
      include /etc/nginx/uwsgi_params;
      uwsgi_pass unix:/path/to/django.socket;
  }
  
  location /ws/ {
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_pass http://unix:/path/to/web.socket;
  }

Since both uWSGI handlers create their own main loop, they also require their own application and
different UNIX sockets. Create two adopter files, one say ``wsgi_django.py``::

  import os
  from django.core.wsgi import get_wsgi_application
  
  os.environ.update(DJANGO_SETTINGS_MODULE='myapp.settings')
  application = get_wsgi_application()

and another, say ``wsgi_websocket.py``::

  import os
  os.environ.update(DJANGO_SETTINGS_MODULE='myapp.settings')
  from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
  
  _app = uWSGIWebsocketServer()
  
  def application(environ, start_response):
      return _app(environ, start_response)

Start two separate uWSGI instances::

  uwsgi --virtualenv /path/to/virtualenv --socket /path/to/django.socket --buffer-size=32768 --workers=5 --master --module wsgi_django
  uwsgi --virtualenv /path/to/virtualenv --http-socket /path/to/web.socket --gevent 1000 --http-websockets --module wsgi_websocket

Your NGiNX server is now configured as a scalable application server which can handle a thousand
websockets connections concurrently.


.. |websocket4redis| image:: _static/websocket4redis.png
.. _psycogreen: https://bitbucket.org/dvarrazzo/psycogreen/
