from django.test import TestCase

from http import HTTPStatus


class ViewTestClass(TestCase):
    def test_error_page_template(self):
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_error_page_status_code(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
