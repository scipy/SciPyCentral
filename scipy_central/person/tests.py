from django.test import TestCase

"""
Tests to add:

* User account: may not contain characters such as #!$&*() etc
* Password must be at least 1 character long
*


"""


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
