from django.test import TestCase

"""
Tests to add:

* User account: may not contain characters such as #!$&*() etc
* Password must be at least 1 character long
* Reset the password; check that email is received;
* Try reset with an incorrect email link
* Reset with correct email link should work
* Reset with correct email link, but enter two different passwords in the form

"""


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
