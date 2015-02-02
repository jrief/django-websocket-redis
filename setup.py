import os
from setuptools import setup, find_packages
from ws4redis import __version__

DESCRIPTION = 'Websocket support for Django using Redis as datastore'

CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 2.7',
]


def read(fname):
    readme_file = os.path.join(os.path.dirname(__file__), fname)
    return os.popen('[ -x "$(which pandoc 2>/dev/null)" ] && pandoc -t rst {0} || cat {0}'.format(readme_file)).read()


setup(
    name='django-websocket-redis',
    version=__version__,
    author='Jacob Rief',
    author_email='jacob.rief@gmail.com',
    description=DESCRIPTION,
    long_description=read('README.md'),
    url='https://github.com/jrief/django-websocket-redis',
    license='MIT',
    keywords=['django', 'websocket', 'redis'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=['examples', 'docs']),
    include_package_data=True,
    install_requires=[
        'setuptools',
        'redis',
        'gevent',
        'greenlet',
        'six',
    ],
    extras_require={
        'uwsgi': ['uWSGI>=1.9.20'],
        'wsaccel': ['wsaccel>=0.6.2'],
        'django-redis-sessions': ['django-redis-sessions>=0.4.0'],
    },
    zip_safe=False,
)
