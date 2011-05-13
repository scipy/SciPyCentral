from django.test import TestCase
from django.test.client import Client

class SimpleTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_basic(self):
        """ Basic testing for the RST -> HTML conversion using Sphinx."""
        response = self.client.post('/rest/', )
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/rest/', {'rst_comment':
                                              'The long cat walked by.'})
        self.assertEqual(response.content, '<p>The long cat walked by.</p>\n')


        response = self.client.get('/rest/', {'rst_comment':
                                              'The long *cat* walked by.'})
        self.assertEqual(response.content,
                         '<p>The long <em>cat</em> walked by.</p>\n')

        response = self.client.get('/rest/', {'rst_comment':
                                              'The long **cat** walked by.'})
        self.assertEqual(response.content,
                         '<p>The long <strong>cat</strong> walked by.</p>\n')

        response = self.client.get('/rest/', {'rst_comment':
                                             'The\n\n* long\n* cat\n* walked'})
        self.assertEqual(response.content,
                        ('<p>The</p>\n<ul class="simple">\n<li>long</li>\n<li>'
                         'cat</li>\n<li>walked</li>\n</ul>\n'))

        response = self.client.get('/rest/', {'rst_comment':
                                             'The http://long.cat.com is ...'})
        self.assertEqual(response.content,
                        ('<p>The <a class="reference external" href="http://'
                         'long.cat.com">http://long.cat.com</a> is ...</p>\n'))