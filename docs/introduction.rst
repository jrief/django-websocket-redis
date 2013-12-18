.. introduction

Introduction
============

Application servers such as Django and Ruby-on-Rails have been developed without intention to create
long living connections. Therefore these frameworks are not a good fit for web applications, which
shall react on asynchronous events initiated by the server. One feasible solution is to continuously
poll the server using an XMLHttpRequest (Ajax) and check if new events shall be delivered. This
however produces a lot of traffic, and depending on the granularity of the polling interval, it is
not a viable solution for real time events such as chat applications or browser based multiplayer
games.

WSGI is a stateless protocol for Python web applications, which means that by design it does not
support non-blocking requests. It defines how to handle requests and making responses in a simple
way abstracted from the HTTP protocol. Most Django installations rely on this workflow:
The web server accepts an incoming request, sets up a WSGI dictionary which then is passed to the
application server. There the HTTP headers and the payload is created and immediately
afterwards the request is finished. This processing typically requires only a few hundred
milliseconds. The throughput, such a server can handle, is the average response time multiplied by
the number of concurrent workers. Each worker requires its own thread/process and a good rule of
thumb is to configure twice as many workers as the number of cores available on that host.
Otherwise you will see a decrease in overall performance, caused by too many context switches
created by the scheduler of the operating system.

Due to this workflow it is almost impossible to add support for long term connections, such as
websockets, on top of the WSGI protocol specification. Therefore most websocket implementations go
for another approach. The websocket connection is controlled by a service running side by side
with the default application server. Here, a webserver with support for long term connections,
dispatches the requests from the clients. A webserver able to dispatch websocket requests is the
NGiNX_ server. Normal requests are sent to Django using the WSGI protocol, whereas the long living
websocket connections are passed over to a special service responsible only for that.

A typical implementation proposal is to use socket.io_ running inside a NodeJS_ loop.

|websocket-nodejs|

Here, Django communicates with Node.JS using a RESTful API, which is ugly because it pulls in two
completely technologies. In alternative proposals, other Python based asynchronous event frameworks
such as Tornado_ or Twisted_ are used. But they all look like makeshift solutions, since one has to
run a second framework side by side with Django. This makes the project dependent on another
infrastructure and having to run two concurrent frameworks can be quite embarrassing during
application development, specially while debugging code.

While searching for a simpler solution, I found out that `uWSGI offers websockets`_ right out of
the box. With Redis_ as message queue, and a few lines of Python code, one can bidirectionally
communicate with any WSGI based framework, for instance **Django**. Of course, here it also is
prohibitive to create a new thread for each open websocket connection. Therefore that part of the
code runs in one single thread/process for all open connections in a cooperative concurrency mode
using the excellent gevent_ and greenlet_ libraries.

This approach has some advantages:

* It is simpler to implement.
* The asynchronous I/O loop handling websockets can run
 * inside Django with ``./manage.py runserver``, giving full debugging control.
 * as a stand alone HTTP server, using uWSGI.
 * using NGiNX as proxy in two decoupled loops, one for WSGI and one for websocket HTTP in front of
   two separate uWSGI workers.
* The whole Django API, such as configuration settings, is available in this loop, provided that no
  blocking calls are made.


Using Redis as a message queue
------------------------------
One might argue that all this is not as simple, since an additional service – the Redis data server
must run side by side with Django. Well, websockets are bidirectional but their normal use case is
to trigger events, send from the server to the client. Remember, the other direction, can be handled 
much easier using Ajax – adding an additional TCP/IP handshake tough.

Here, the only “stay in touch with the client” is the websocket. And since we speak about hundreds
or thousands of open connections, the footprint in terms of memory and CPU resources must be brought
down to a minimum. With this implementation, only two file descriptors are required for each open
connection, one which stays in touch with the client and one which wait for events delivered by
a message queue.

Productive webservers require a some kind of session store anyway. This can be a memcached_ or a
or Redis data server. Therefore, such a service must run anyway and if we can choose between one
them, we shall use one with integrated message queuing support. So, by using Redis, the message
queue required for websocket communication, is effectively free.

.. _NodeJS: http://nodejs.org/
.. _socket.io: http://socket.io/
.. _Tornado: http://www.tornadoweb.org/
.. _Twisted: http://twistedmatrix.com/
.. _uWSGI offers websockets: http://uwsgi-docs.readthedocs.org/en/latest/WebSockets.html
.. _Redis: http://redis.io/
.. _memcached: http://memcached.org/
.. _gevent: http://www.gevent.org/
.. _greenlet: http://greenlet.readthedocs.org/
.. |websocket-nodejs| image:: _static/websocket-nodejs.png
