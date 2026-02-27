import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_content_security_policy(clinical_user_client):
    """
    Test that the Content-Security-Policy HTTP response header is correctly set.

    The policy is configured by CONTENT_SECURITY_POLICY in settings.py
    """
    response = clinical_user_client.http.get(reverse("clinics:index"))
    assert response.status_code == 200

    expected_directives = {
        "connect-src 'self'",
        "script-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "style-src 'self'",
        "default-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "font-src 'self' https://assets.nhs.uk",
    }

    csp_header = response.headers["content-security-policy"]
    actual_directives = {d.strip() for d in csp_header.split(";")}

    assert expected_directives == actual_directives
