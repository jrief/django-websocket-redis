.. _installation_and_configuration:

Installation and Configuration
==============================

Getting the latest release
--------------------------

Installation
------------
If not already done, install Redis_, using your operation systems tools such as ``aptitude``,
``yum``, ``port`` or `install Redis from source`_.

Start the Redis service 

The latest stable release as found on PyPI::

  pip install django-websocket-redis

or the newest development from github::

  pip install -e git+https://github.com/jrief/django-websocket-redis#egg=django-websocket-redis

Dependencies
------------
* `Django`_ >=1.5
* `Redis`_


Configuration
-------------

Add ``"djangular"`` to your project's ``INSTALLED_APPS`` setting, and make sure that static files
are found in external Django apps::

  INSTALLED_APPS = (
      ...
      'djangular',
      ...
  )
  
  STATICFILES_FINDERS = (
      'django.contrib.staticfiles.finders.FileSystemFinder',
      'django.contrib.staticfiles.finders.AppDirectoriesFinder',
      ...
  )

.. note:: **django-angular** does not define any database models. It can therefore easily be
          installed without any database synchronization.

.. _github: https://github.com/jrief/django-angular
.. _Django: http://djangoproject.com/
.. _AngularJS: http://angularjs.org/
.. _pip: http://pypi.python.org/pypi/pip
