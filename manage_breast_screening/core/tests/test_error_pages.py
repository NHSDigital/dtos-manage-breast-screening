from django.test import RequestFactory, TestCase, override_settings

from manage_breast_screening.core.views.errors import page_not_found, server_error


@override_settings(DEBUG=False)
class ErrorPageTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_404_page(self):
        request = self.factory.get("/not-a-real-url/")
        response = page_not_found(request, exception=None)
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page not found", response.content)

    def test_500_page(self):
        request = self.factory.get("/")
        response = server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"There is a problem with the service", response.content)
