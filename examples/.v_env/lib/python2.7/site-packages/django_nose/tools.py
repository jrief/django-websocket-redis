# coding: utf-8
# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

"""
Provides Nose and Django test case assert functions
"""

from __future__ import unicode_literals

from django.test.testcases import TransactionTestCase


import re

## Python

from nose import tools
for t in dir(tools):
    if t.startswith('assert_') or t in ('ok_', 'eq_'):
        vars()[t] = getattr(tools, t)

del tools
del t

## Django

camelcase = re.compile('([a-z][A-Z]|[A-Z][a-z])')

def insert_underscore(m):
    a, b = m.group(0)
    if b.islower():
        return '_{}{}'.format(a, b)
    else:
        return '{}_{}'.format(a, b)

def pep8(name):
    return camelcase.sub(insert_underscore, name).lower()

class Dummy(TransactionTestCase):
    def nop():
        pass
_t = Dummy('nop')

for at in [ at for at in dir(_t)
            if at.startswith('assert') and not '_' in at ]:
    pepd = pep8(at)
    vars()[pepd] = getattr(_t, at)

del re
del insert_underscore
del camelcase
del Dummy
del TransactionTestCase
del _t
del at
del pep8
del pepd

## New

def assert_code(response, status_code, msg_prefix=''):
    """Asserts the response was returned with the given status code
    """

    if msg_prefix:
        msg_prefix = '%s: ' % msg_prefix

    assert response.status_code == status_code, \
        'Response code was %d (expected %d)' % \
            (response.status_code, status_code)

def assert_ok(response, msg_prefix=''):
    """Asserts the response was returned with status 200 (OK)
    """

    return assert_code(response, 200, msg_prefix=msg_prefix)

def assert_mail_count(count, msg=None):
    """Assert the number of emails sent.
    The message here tends to be long, so allow for replacing the whole
    thing instead of prefixing.
    """
    from django.core import mail

    if msg is None:
        msg = ', '.join([e.subject for e in mail.outbox])
        msg = '%d != %d %s' % (len(mail.outbox), count, msg)
    assert_equals(len(mail.outbox), count, msg)

# EOF

