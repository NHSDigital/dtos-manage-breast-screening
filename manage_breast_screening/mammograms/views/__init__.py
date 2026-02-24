import os

from manage_breast_screening.gateway.models import Relay


def gateway_images_enabled(appointment):
    """Check if automatic gateway image retrieval is enabled."""
    if os.getenv("GATEWAY_IMAGES_ENABLED", "false").lower() == "true":
        return Relay.for_provider(appointment.provider) is not None
    return False
