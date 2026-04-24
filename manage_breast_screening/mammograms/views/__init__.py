from openfeature import api

from manage_breast_screening.gateway.models import Relay


def gateway_images_enabled(appointment):
    """Check if automatic gateway image retrieval is enabled."""
    feature_flags = api.get_client()
    if feature_flags.get_boolean_value("gateway_images", False):
        return Relay.for_appointment(appointment) is not None
    return False
