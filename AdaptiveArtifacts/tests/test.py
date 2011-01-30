"""
class X:
    pass

class Y:
    pass
"""
class A():
    def __init__(self):
        print "a"
        self.attr1 = 1
        
class B(A):
    pass

class MetaStuff(type):
    pass

a = A()

print type(A).__base__.__base__
print type(A).__base__.__class__.__base__
print type(A).__base__.__class__
print type(type(A).__base__.__class__)
print type(A).__base__.__class__.__class__
print type(A).__bases__
print type(a).__bases__
print A.__bases__
print type(A)
print type(B)
print type(a)
print type(type(A))
print type(type(a))
print a.__class__
print type(a.__class__)
print a.__class__ is A
print type(A).__class__
print type(a).__class__
print dir(A)
print dir(B)
print A.__bases__
print B.__bases__
print dir(type(A))
print dir(type(B))
print dir(type(a))

"""
print a.__class__
print dir(a)
print dir(a.__class__)
#print dir(a.__metaclass__)
print dir(type)
print type.__base__
print type.__bases__
print type.__class__
print type.__name__
print type.__subclasses__
"""
