from django.test import TestCase
from django.core.urlresolvers import reverse


class TextExistance(TestCase):
    def test_page_exists(self):

        # Main page
        response = self.client.get(reverse('spc-main-page'))
        self.assertEqual(response.status_code, 200)

        # About page
        response = self.client.get(reverse('spc-about-page'))
        self.assertEqual(response.status_code, 200)

        # Licences page
        response = self.client.get(reverse('spc-about-licenses'))
        self.assertEqual(response.status_code, 200)
