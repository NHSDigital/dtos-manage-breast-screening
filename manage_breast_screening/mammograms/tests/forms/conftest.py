import pytest
from django.test import RequestFactory


@pytest.fixture
def dummy_request(clinical_user):
    request = RequestFactory().get("/test-form")
    request.user = clinical_user
    return request
