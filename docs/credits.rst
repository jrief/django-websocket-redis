.. credits

=================
Credits to Others
=================

When Jacob Kaplan-Moss gave his `keynote talk`_ on PyCon 2013 Canada, he mentioned the MeteorJS_
framework as the next big step in web development.

.. _keynote talk: http://www.youtube.com/watch?v=UKAkKXFMQP8#t=1174
.. _MeteorJS: https://www.meteor.com/

Personally, I share his opinion about this forecast. The point for both of us is, that we don't
see JavaScript as *the* server side language – yet. Probably I am wrong on this, but for the
moment I prefer server side frameworks in a language with real classes and numeric types suitable
for business applications. This all is missing in JavasSript. Moreover, if content has to be
optimized for `E-book readers`_, static rendering on the server side becomes mandatory.

.. _E-book readers: http://en.wikipedia.org/wiki/E-book_reader

Apart from these technical issues, I love clear separation of concerns, where I can deliberately
exchange software components specialized for the running platform. Eventually a web server is very
different from a browser, so why should I be forced to run components from the same framework on
both of them? If this would be the case, frameworks such as GWT_ would be more successful.

.. _GWT: http://www.gwtproject.org/

Therefore my way to go, is for a pure server- and a pure client-side framework. As the latter,
I prefer AngularJS_, which in my humble opinion is by far the best JavaScript framework ever written.

.. _AngularJS: http://angularjs.org/


AngularJS
=========

is a MVC framework for the client with two-way data-binding. Two way data-binding is an automatic
way of updating the view whenever the model changes, as well as updating the model whenever the view
changes. Django users will immediately feel comfortable with AngularJS, since the concept of
templates, controllers and data models is quite similar.

The problem however with two distinct frameworks is, that it becomes difficult to use the server
side model on the client, and always keeping track on each model alteration on the server. This by
the way, is a typical violation of the DRY principle and should be avoided. I therefore wrote a
library, django-angular_, which “translates” Django models into an Angular models and vice versa.
With this library, for instance, it is possible to use a Django form and bind it with an AngularJS
controller without having to keep track on each of the model fields. It is even possible to “export”
Django's server side form validation to the client side validation functions, without having to
duplicate this code.

.. _django-angular: https://github.com/jrief/django-angular


Current solutions
=================

For rendering server side data using HTML, and receiving client data through POST or
XMLHttpRequests, **django-angular** works fine, but in order to update data on the client upon
events triggered by the server, communication using a technology such as websockets must be provided
by the application server.

I tried out all of the current implementations to add functionality for websocket to Django. But
they all looked like makeshift solutions. Something I found specially disturbing, was the need for
another framework running side by side with Django, during development.


uWSGI
=====

Then I stumbled across a talk_ from Roberto De Ioris on EuroPython 2013.

.. _talk: http://www.youtube.com/watch?v=qmdk5mVLsHM#t=580

Here he pointed out, that the WSGI protocol will never be able to support a technology such as
websockets. But, since websockets override HTTP, the solution is to let them override WSGI too.
Now with a web application runner, supporting thousands of concurrent websocket connections, the
implementation for Django was quite easy. Adding a compatible solution for the development
environment on Django was somehow trickier, but fortunately Jeffrey Gelens had already implemented
a pure Python implementation, which can do the complicated `websocket handshake`_ for us.

.. _websocket handshake: https://bitbucket.org/Jeffrey/gevent-websocket

Since these technologies now can be sticked together, adding three-way data-binding for AngularJS
will be the next step. Three-way data-binding is an extension to synchronize changes on the Angular
model back to a data-store at the server side. This is awesome because then Django can manipulate
the client side DOM, using the AngularJS template system but without having to implement a single
line of JavaScript code. With three-way data-binding, Django will come a step nearer to one of the
coolest feature MeteorJS can offer right now.
