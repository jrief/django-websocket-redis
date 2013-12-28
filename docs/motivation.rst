.. motivation

Motivation for this project
===========================

When Jacob Kaplan-Moss gave his keynote on PyCon 2013 Canada, he mentioned the MeteorJS_ framework
as the next big thing. In his opinion, web development will go in that direction.

.. youtube:: http://www.youtube.com/watch?v=UKAkKXFMQP8#t=1174

Personally, I share his opinion about this forecast. The point for both of us however is, that we
don't see JavaScript as *the* server side language yet. Probably I am wrong on this, but for the
moment I prefer server side frameworks, which can work on their own, in a language with real
classes. Therefore my way to go for a JavaScript framework is not not MeteorJS but AngularJS_,
which in my humble opinion is by far the best client side framework ever written.

AngularJS
---------
is a MVC framework for the client with two-way data-binding. Django users will immediately feel
comfortable with AngularJS, since the concept of templates, controllers and data models is quite
similar.

The problem however with two distinct frameworks is, that it becomes difficult to use the server
side model on the client, and always keeping track on each model alteration on the server. This by
the way is a typical violation of the DRY principle and should be avoided. I therefore wrote a
library, django-angular_, which “translates” Django models into an Angular models and vice versa.
With this library, for instance, it is possible to use a Django form and bind it with an Angular
controller without having to keep track on each of the model fields.

Current solutions
-----------------
For rendering server side data using HTML, and receiving client data through POST or
XMLHttpRequests, **django-angular** works fine, but in order to update data on the client upon
events triggered by the server, communication using a technology such as websockets must be provided
by the application server.

I tried out all of the current implementations to add functionality for websocket to Django. But
they all looked like makeshift solutions. Something I found specially disturbing, was the need for
another framework running side by side with Django, during development.

uWSGI
-----
Then I stumbled across this talk Roberto De Ioris gave on EuroPython 2013:

.. youtube:: http://www.youtube.com/watch?v=qmdk5mVLsHM#t=580

Here he pointed out, that the WSGI protocol will never be able to support a technology such as
websockets. But, since websockets override HTTP, the solution is to let them override WSGI too.
Now with an application runner, supporting thousands of concurrent websocket connections, the
implementation for Django was quite easy. Adding a compatible solution for the development
environment on Django was somehow trickier, but fortunately Jeffrey Gelens had already implemented
a pure Python implementation, which can do the handshake for websockets`_.

Since these technologies now can be sticked together, adding three-way data-binding for AngularJS
will be the next step. Two way data-binding is an automatic way of updating the view whenever the
model changes, as well as updating the model whenever the view changes. Three-way data-binding
is to synchronize these changes with a data-store at the server side. This is awesome because then
Django can manipulate the DOM, using Angulars template system but without having to implement a
single line of JavaScript code. With three-way data-binding, Django will come a step nearer to one
of the coolest feature MeteorJS can offer right now.

.. _MeteorJS: https://www.meteor.com/
.. _AngularJS: http://angularjs.org/
.. _django-angular: https://github.com/jrief/django-angular
.. _Python implementation for websockets: https://bitbucket.org/Jeffrey/gevent-websocket
