.. api

=================================
Application Programming Interface
=================================

This document describes how to interact with **Websockets for Redis** from the Django loop and how
to adopt the Websocket loop for other purposes.

Use ``RedisPublisher`` from inside Django views
===============================================
For obvious architectural reasons, the code handling the websocket loop can not be accessed directly
from within Django. Therefore, all communication from Django to the websocket loop, must be passed
over to the Redis message queue and vice versa. To facility this, **ws4redis** offers a class named
``RedisPublisher``. An instance of this class shall be used from inside Django views to push
messages via a websocket to the client, or to fetch persisted messages sent through the websocket.

Example view:

.. code-block:: python

	from django.views.generic.base import View
	from ws4redis.publisher import RedisPublisher

	class MyTypicalView(View):
	    facility = 'unique-named-facility'
	    audience = {'broadcast': True}
	
	    def __init__(self, *args, **kwargs):
	        super(MyTypicalView, self).init(*args, **kwargs)
	        self.redis_publisher = RedisPublisher(facility=self.facility, **self.audience)

	    def get(self, request)
	        message = 'A message passed to all browsers listening on the named facility'
	        self.redis_publisher.publish_message(message)

For further options, refer to the reference:

.. autoclass:: ws4redis.publisher.RedisPublisher
   :members:

.. automethod:: ws4redis.redis_store.RedisStore.publish_message


Replace ``RedisSubscriber`` for the Websocket loop
--------------------------------------------------
Sometimes the predefined channels for subscribing and publishing messages might not be enough.
If there is a need to add additional channels to the message queue, it is possible to replace
the implemented class ``ws4redis.store.RedisSubscriber`` by setting the configuration directive
``WS4REDIS_SUBSCRIBER`` to a class of your choice.

Use the class ``RedisSubscriber`` as a starting point and overload the required methods with your
own implementation.

.. autoclass:: ws4redis.subscriber.RedisSubscriber
   :members:

.. warning:: If the overloaded class calls any blocking functions, such as ``sleep``, ``read``,
       ``select`` or similar, make sure that these functions are patched by the gevent library,
       otherwise *all* connections will block simultaneously.

