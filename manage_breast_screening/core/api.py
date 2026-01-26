import os
from functools import wraps

from ninja import NinjaAPI

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


api = NinjaAPI(title="Manage Breast Screening API", version="1.0.0")
api.add_router("/dicom/", dicom_router, tags=["DICOM"])
api.add_decorator(check_availability())
dicom_router.add_decorator(check_availability())


@api.get(
    "/status", response={200: StatusResponse, 403: StatusResponse}, tags=["Status"]
)
def status(request):
    return 200, {"status": "API is available"}
