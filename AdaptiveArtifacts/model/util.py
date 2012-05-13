# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.

def to_valid_identifier_name(name):
    """
    Uses "name" to create a valid python identifier by removing illegal
    characters, as described in:
    http://docs.python.org/reference/lexical_analysis.html#identifiers

    Ultimately, the identifiers could be semantically opaque but, for
    eased debugging, it's handy if they're not. As this process doesn't
    produce identifiers that can be guaranteed to unique, we suffix it
    with a hash to ensure it doesn't clash with other identifiers.
    """
    def gen_valid_identifier(seq):
        itr = iter(seq)
        # pull characters until we get a legal one for first in identifer
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
    import hashlib
    return ''.join(gen_valid_identifier(name)) + "_" + hashlib.md5(name).hexdigest()

class classinstancemethod(object):
    """
    Acts like a class method when called from a class, like an
    instance method when called by an instance.  The method should
    take two arguments, 'self' and 'cls'. 'self' will be None if
    called via class, but they will both have values if called via
    instance. See http://stackoverflow.com/a/10413769/684253
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
