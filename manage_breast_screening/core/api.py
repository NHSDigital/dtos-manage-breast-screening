import hmac
import os
from functools import wraps

from ninja import NinjaAPI
from ninja.security import HttpBearer

from manage_breast_screening.dicom.api import router as dicom_router

from .api_schema import StatusResponse


def check_availability():
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not os.getenv("API_ENABLED", "true").lower() == "true":
                return 403, {"status": "API is not available"}
            return func(request, *args, **kwargs)

        return wrapper

    return decorator


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        expected_token = os.getenv("API_AUTH_TOKEN")
        if not expected_token:
            return None
        if hmac.compare_digest(token, expected_token):
            return token


api = NinjaAPI(auth=GlobalAuth(), title="Manage Breast Screening API", version="1.0.0")
api.add_router("/dicom/", dicom_router, tags=["DICOM"])
api.add_decorator(check_availability())
dicom_router.add_decorator(check_availability())


@api.get(
    "/status", response={200: StatusResponse, 403: StatusResponse}, tags=["Status"]
)
def status(request):
    return 200, {"status": "API is available"}
