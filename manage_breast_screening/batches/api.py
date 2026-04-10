import hmac
import logging
import os
from functools import wraps

import ninja
from ninja import NinjaAPI
from ninja.security import HttpBearer

from manage_breast_screening.batches.models import BatchPayload
from manage_breast_screening.batches.services import BatchService
from manage_breast_screening.core.api_schema import ErrorResponse, StatusResponse

logger = logging.getLogger(__name__)


class SuccessResponse(ninja.Schema):
    bss_batch_id: str


def check_availability():
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if os.getenv("BATCH_API_ENABLED", "true").lower() != "true":
                return 403, {"status": "API is not available"}
            return func(request, *args, **kwargs)

        return wrapper

    return decorator


class BatchAuth(HttpBearer):
    def authenticate(self, request, token):
        expected_token = os.getenv("BATCH_API_AUTH_TOKEN")
        if not expected_token:
            return None
        if hmac.compare_digest(token, expected_token):
            return token


batch_api = NinjaAPI(
    auth=BatchAuth(),
    title="Manage Breast Screening Batch API",
    version="1.0.0",
    urls_namespace="batch_api",
)
batch_api.add_decorator(check_availability())


@batch_api.post(
    "",
    response={
        201: SuccessResponse,
        403: StatusResponse,
        500: ErrorResponse,
    },
)
def create_batch(request, payload: BatchPayload):
    """
    Create a new Batch with the provided Batch data.

    Returns 201 Created on success.
    """
    try:
        batch = BatchService.create_batch_from_payload(payload)
    except Exception as e:
        logger.error(f"Error creating batch: {e}")
        return 500, {
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An error occurred while creating the batch",
        }

    return 201, {"bss_batch_id": batch.bss_batch_id}
