import unittest

class Test(object):
    a=1
    def method_one(self):
        print "Called method_one"
    @staticmethod
    def method_two():
        print "Called method_two"
    @classmethod
    def method_three(cls):
        cls.method_two()
    @classmethod
    def method_four(cls):
        print cls.a
    @classmethod
    def get_meta_name(cls):
        """
        Returns the name used to identify the representation of this class in the pool.
        """
        return cls.__name__
class T2(Test):
    a=2
    @staticmethod
    def method_two():
        print "T2"


class QuickSpike(unittest.TestCase):
    def testA(self):
        a_test = Test()
        a_test.method_one()
        a_test.method_two()
        a_test.method_three()
        b_test = T2()
        b_test.method_three()
        Test.method_two()
        T2.method_three()
        Test.method_four()
        T2.method_four()
        print Test.get_meta_name()
        print T2.get_meta_name()
        print a_test.get_meta_name()
        print b_test.get_meta_name()
        print a_test.__class__.__name__
        print b_test.__class__.__name__

if __name__ == "__main__":
    unittest.main()