import os
from functools import wraps
from typing import Any

import ninja
import pydicom
from ninja import File, Router
from ninja.files import UploadedFile

from .dicom_recorder import DicomRecorder

router = Router(auth=None)


class ErrorResponse(ninja.Schema):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str | None = None


class SuccessResponse(ninja.Schema):
    study_instance_uid: str
    series_instance_uid: str
    sop_instance_uid: str
    instance_id: Any


class StatusResponse(ninja.Schema):
    status: str


def check_availability():
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not os.getenv("DICOM_API_ENABLED", "true").lower() == "true":
                return 403, {"status": "DICOM API is not available"}
            return func(request, *args, **kwargs)

        return wrapper

    return decorator


router.add_decorator(check_availability())


@router.get("/status", response={200: StatusResponse, 403: StatusResponse})
def status(request):
    return 200, {"status": "DICOM API is available"}


@router.put(
    "/upload",
    response={
        201: SuccessResponse,
        400: ErrorResponse,
        403: StatusResponse,
        500: ErrorResponse,
    },
)
def upload(request, file: File[UploadedFile]):
    """
    Accepts PUT with a single DICOM file in form field 'file'
    """
    source_message_id = request.META.get("HTTP_X_Source_Message_ID")
    if not source_message_id:
        return 400, {
            "title": "Missing X-Source-Message-ID header",
            "status": 400,
            "detail": "The X-Source-Message-ID header is required.",
        }

    dicom_file = request.FILES.get("file")
    if dicom_file is None:
        return 400, {
            "title": "No file uploaded",
            "status": 400,
            "detail": "A DICOM file must be uploaded in the 'file' form field.",
        }

    try:
        study, series, image = DicomRecorder.get_or_create_records(
            source_message_id, dicom_file
        )

    except pydicom.errors.InvalidDicomError:
        return 400, {
            "title": "Invalid DICOM file",
            "status": 400,
            "detail": "The uploaded file is not a valid DICOM file.",
        }
    except AttributeError:
        return 400, {
            "title": "Missing DICOM attributes",
            "status": 400,
            "detail": "The DICOM file is missing required UID attributes.",
        }
    except Exception as e:
        return 500, {
            "title": "Internal Server Error",
            "status": 500,
            "detail": f"An unexpected error occurred: {str(e)}",
        }

    return 201, {
        "study_instance_uid": study.study_instance_uid,
        "series_instance_uid": series.series_instance_uid,
        "sop_instance_uid": image.sop_instance_uid,
        "instance_id": image.id,
    }
