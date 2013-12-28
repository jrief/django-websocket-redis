.. api

Application Programming Interface
=================================
Sometimes the six predefined channels for subscribing and publishing messages is not enough. If
there is some need to add additional channels to the message queue, it is possible to replace the
implemented class ``ws4redis.store.RedisStore`` by setting the configuration directive
``WS4REDIS_STORE`` to a class of your choice.

A good class to start with is ``ws4redis.store.RedisStore``. Overload the required methods with
your own implementation.

.. autoclass:: ws4redis.store.RedisStore
   :members:
