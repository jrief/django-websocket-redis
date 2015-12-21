#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages
from ws4redis import __version__
try:
    from pypandoc import convert
except ImportError:
    import io

    def convert(filename, fmt):
        with io.open(filename, encoding='utf-8') as fd:
            return fd.read()

DESCRIPTION = 'Websocket support for Django using Redis as datastore'

CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Framework :: Django :: 1.5',
    'Framework :: Django :: 1.6',
    'Framework :: Django :: 1.7',
    'Framework :: Django :: 1.8',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
]

setup(
    name='django-websocket-redis',
    version=__version__,
    author='Jacob Rief',
    author_email='jacob.rief@gmail.com',
    description=DESCRIPTION,
    long_description=convert('README.md', 'rst'),
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
