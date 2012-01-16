import uuid

def is_uuid(value):
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True

class Proxy(object):
    def __init__(self, subject):
        self.__subject = subject
    def __getattr__(self, name ):
        return getattr(self.__subject, name)