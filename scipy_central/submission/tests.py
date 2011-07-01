"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
import re

class SimpleTest(TestCase):
    def test_url_matches(self):

        view_url = r'^(?P<item_id>\d+)+(/)?(?P<rev_num>\d+)?(/)?(?P<slug>[-\w]+)?(/)?'
        view_url = re.compile(view_url)

        valid_items = [
           ('2',         {'item_id':'2', 'rev_num':None, 'slug': None}),
           ('007',       {'item_id':'007', 'rev_num':None, 'slug': None}),
           ('007/',      {'item_id':'007', 'rev_num':None, 'slug': None}),
           ('23/',       {'item_id':'23', 'rev_num':None, 'slug': None}),
           ('23/4',      {'item_id':'23', 'rev_num':'4', 'slug': None}),
           ('23/42',     {'item_id':'23', 'rev_num':'42', 'slug': None}),
           ('23/008/',   {'item_id':'23', 'rev_num':'008', 'slug': None}),
           ('23/9/asd',  {'item_id':'23', 'rev_num':'9', 'slug': 'asd'}),
           ('53/09/a-w', {'item_id':'53', 'rev_num':'09', 'slug': 'a-w'}),
           ('53/09/a-w/',{'item_id':'53', 'rev_num':'09', 'slug': 'a-w'}),
           ('53/09/a_w/',{'item_id':'53', 'rev_num':'09', 'slug': 'a_w'}),
           ('53/09/2_w/',{'item_id':'53', 'rev_num':'09', 'slug': '2_w'}),
        ]

        for item in valid_items:
            match = view_url.match(item[0]).groupdict()
            for key, val in match.iteritems():
                self.assertEqual(val, item[1][key])



