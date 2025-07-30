import base64


def parse_basic_auth(auth):
    """
    Helper to parse a HTTP_AUTHORIZATION header for basic authentication

    See https://datatracker.ietf.org/doc/html/rfc7617
    """
    scheme, encoded_string = auth.split()

    if scheme.lower() != "basic":
        raise ValueError

    username, password = base64.b64decode(encoded_string).decode("utf-8").split(":", 1)

    return username, password
