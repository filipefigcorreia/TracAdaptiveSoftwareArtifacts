# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

import unicodedata
import hashlib

def to_valid_identifier_name(name):
    """
    Uses "name" to create a valid python identifier by removing illegal
    characters, as described in:
    http://docs.python.org/reference/lexical_analysis.html#identifiers

    Ultimately, the identifiers could be semantically opaque but, for
    eased debugging, it's handy if they're not. As this process doesn't
    produce identifiers that can be guaranteed to be unique, we suffix
    them with a hash to ensure they don't clash with other identifiers.
    """
    def gen_valid_identifier(seq):
        seq = unicodedata.normalize('NFKD', seq).encode('ascii','ignore')
        itr = iter(seq)
        # pull characters until we get a legal one for first in identifier
        for ch in itr:
            if ch == '_' or ch.isalpha():
                yield ch
                break
        # pull remaining characters and yield legal ones for identifier
        for ch in itr:
            if ch == ' ':
                ch = '_'
            if ch == '_' or ch.isalpha() or ch.isdigit():
                yield ch
    return str(''.join(gen_valid_identifier(name)) + "_" + hashlib.md5(name.encode("utf-8")).hexdigest())

class classinstancemethod(object):
    """
    Decorator that makes a given method act like a class method when
    called for a class, and like an instance method when called for
    an instance. The method should take two arguments, 'self' and
    'cls'. 'self' will be None if called via class, but they will
    both have values if called via instance.
    See http://stackoverflow.com/a/10413769/684253
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, type=None):
        return _methodwrapper(self.func, obj=obj, type=type)

class _methodwrapper(object):
    def __init__(self, func, obj, type):
        self.func = func
        self.obj = obj
        self.type = type

    def __call__(self, *args, **kw):
        assert 'self' not in kw and 'cls' not in kw, (
            "You cannot use 'self' or 'cls' arguments to a "
            "classinstancemethod")
        return self.func(*((self.obj, self.type) + args), **kw)

    def __repr__(self):
        if self.obj is None:
            return ('<bound class method %s.%s>'
                    % (self.type.__name__, self.func.func_name))
        else:
            return ('<bound method %s.%s of %r>'
                    % (self.type.__name__, self.func.func_name, self.obj))
