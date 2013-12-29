.. api

Application Programming Interface
=================================
Sometimes the six predefined channels for subscribing and publishing messages might not be enough.
If there is some need to add additional channels to the message queue, it is possible to replace
the implemented class ``ws4redis.store.RedisStore`` by setting the configuration directive
``WS4REDIS_STORE`` to a class of your choice.

Use the class ``RedisStore`` as a starting point and overload the required methods with your own
implementation.

.. autoclass:: ws4redis.store.RedisStore
   :members:

.. warning:: If the overloaded class calls any blocking functions, such as ``sleep``, ``read``,
       ``select`` or similar, make sure that these functions are patched by the gevent library,
       otherwise *all* connections will block simultaneously.
