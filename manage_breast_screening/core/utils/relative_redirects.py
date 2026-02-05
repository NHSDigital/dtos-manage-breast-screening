from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme


def extract_relative_redirect_url(
    request, default=None, parameter_name="return_url"
) -> str:
    """
    Extracts a relative redirect path from the request's POST or GET data.

    This function retrieves the value of `parameter_name` (default: "return_url") from the request.
    It validates that the URL is safe for redirection by ensuring:
      - It is allowed by Django's `url_has_allowed_host_and_scheme` (prevents open redirects).
      - It starts with a forward slash ("/"), ensuring it is a relative path.

    If the URL is not present or not safe, the provided `default` value is returned.

    Args:
        request: The Django HttpRequest object.
        default: The value to return if no safe redirect path is found.
        parameter_name: The name of the parameter to look for in POST or GET data.

    Returns:
        A relative redirect path as a string, or the default value if not found or unsafe.
    """
    return_url = request.POST.get(parameter_name) or request.GET.get(parameter_name)

    if (
        return_url
        and url_has_allowed_host_and_scheme(return_url, allowed_hosts=None)
        and return_url.startswith("/")
    ):
        return iri_to_uri(return_url)
    else:
        return default
