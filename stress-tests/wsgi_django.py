# run uWSGI behind NGiNX as:
#! uwsgi --virtualenv /path/to/virtualenv --socket /var/tmp/django.socket --buffer-size=32768 --umask 000 --workers=2 --master --module wsgi_django
import os
import sys
sys.path[0:0] = [os.path.abspath('..'), os.path.abspath('../examples')]
os.environ.update(DJANGO_SETTINGS_MODULE='chatserver.settings')
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
