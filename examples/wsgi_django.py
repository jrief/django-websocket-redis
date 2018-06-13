# Django with WebSockets for Redis behind NGiNX using uWSGI
# (for sites requiring scalability)
# 
# Note: this is entry point for the Django loop
#
# uwsgi --virtualenv /path/to/virtualenv --socket /path/to/django.socket --buffer-size=32768 --workers=5 --master --module wsgi_django
# 
# See: http://django-websocket-redis.readthedocs.io/en/latest/running.html#django-with-websockets-for-redis-behind-nginx-using-uwsgi

import os
os.environ.update(DJANGO_SETTINGS_MODULE='chatserver.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
