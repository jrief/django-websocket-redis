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
]


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


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
        'Django>=1.5',
        'uWSGI>=1.9.20',
        'setuptools',
        'redis',
        'gevent',
        'greenlet',
        # optional 'wsaccel'
    ],
)
