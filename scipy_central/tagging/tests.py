from django.test import TestCase
from models import Tag

class RepeatedTag(TestCase):
    def test_adding_repeated_tag(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        t1, _ = Tag.objects.get_or_create(name='testing tag')
        t2, _ = Tag.objects.get_or_create(name='testing tag')
        self.assertEqual(t1.id, t2.id)