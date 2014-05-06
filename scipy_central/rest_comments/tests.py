from django.test import TestCase
from django.test.client import Client

from django.core.urlresolvers import reverse

class SimpleTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_basic(self):
        """ Basic testing for the RST -> HTML conversion using Sphinx."""
        response = self.client.post(reverse('spc-rest-convert'),)
        self.assertEqual(response.status_code, 404)


        response = self.client.get(reverse('spc-rest-convert'), 
                                   {'rest_text': 'The long cat walked by.',
                                    'source': 'simpletest'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.content, 
                        '{"html_text": "<p>The long cat walked by.</p><br>", '
                        '"success": true}')


        response = self.client.get(reverse('spc-rest-convert'), 
                                   {'rest_text': 'The long *cat* walked by.',
                                    'source': 'simpletest'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.content,
                         '{"html_text": "<p>The long <em>cat</em> walked by.</p><br>", '
                         '"success": true}')


        response = self.client.get(reverse('spc-rest-convert'), 
                                   {'rest_text': 'The long **cat** walked by.',
                                    'source': 'simpletest'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.content,
                         '{"html_text": "<p>The long <strong>cat</strong> walked by.</p><br>", '
                         '"success": true}')


        response = self.client.get(reverse('spc-rest-convert'), 
                                   {'rest_text': 'The\n\n* long\n* cat\n* walked',
                                    'source': 'simpletest'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.content,
                        ('{"html_text": "<p>The</p><br><ul class=\\"simple\\"><br><li>long</li>'
                         '<br><li>cat</li><br><li>walked</li><br></ul><br>", "success": true}'))

        
        response = self.client.get(reverse('spc-rest-convert'), 
                                   {'rest_text': 'The http://long.cat.com is ...',
                                    'source': 'simpletest'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.content,
                        ('{"html_text": "<p>The <a class=\\"reference external\\" '
                         'href=\\"http://long.cat.com\\">http://long.cat.com</a> is '
                         '...</p><br>", "success": true}'))
        

        response = self.client.get(reverse('spc-rest-convert'), 
                                   {'rest_text': 'The ``long cat`` walked',
                                    'source': 'simpletest'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.content,
                        ('{"html_text": "<p>The <tt class=\\"docutils literal\\">'
                         '<span class=\\"pre\\">long</span> <span class=\\"pre\\">cat</span>'
                         '</tt> walked</p><br>", "success": true}'))
        

        response = self.client.get(reverse('spc-rest-convert'), 
                                   {'rest_text': 'The::\n\n\tlong\n\tcat\n\n is',
                                    'source': 'simpletest'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.content,
                        ('{"html_text": "<p>The:</p><br><div class=\\"highlight-python\\">'
                         '<div class=\\"highlight\\"><pre>   long<br>   cat<br><br>is<br>'
                         '</pre></div><br></div><br>", "success": true}'))