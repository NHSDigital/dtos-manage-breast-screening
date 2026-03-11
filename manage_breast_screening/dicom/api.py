import logging
from typing import Any

import ninja
import pydicom
from django.utils import timezone
from ninja import File, Router
from ninja.files import UploadedFile

from manage_breast_screening.core.api_schema import ErrorResponse, StatusResponse
from manage_breast_screening.gateway.models import GatewayAction, GatewayActionStatus

from .dicom_recorder import DicomRecorder

router = Router()

logger = logging.getLogger(__name__)


class SuccessResponse(ninja.Schema):
    study_instance_uid: str
    series_instance_uid: str
    sop_instance_uid: str
    instance_id: Any


class FailurePayload(ninja.Schema):
    error: str


@router.put(
    "/{source_message_id}",
    response={
        201: SuccessResponse,
        400: ErrorResponse,
        403: StatusResponse,
        500: ErrorResponse,
    },
)
def upload(request, source_message_id: str, file: File[UploadedFile]):
    """
    Accepts PUT with a single DICOM file in form field 'file'
    """
    max_size = 100 * 1024 * 1024
    if file.size > max_size:
        return 400, {
            "title": "File too large",
            "status": 400,
            "detail": "The file cannot be larger than 100MB",
        }

    if file is None:
        return 400, {
            "title": "No file uploaded",
            "status": 400,
            "detail": "A DICOM file must be uploaded in the 'file' form field.",
        }

    try:
        study, series, image = DicomRecorder.get_or_create_records(
            source_message_id, file
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
        logger.error("Error processing DICOM file: %s", e, exc_info=True)
        return 500, {
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred.",
        }

    return 201, {
        "study_instance_uid": study.study_instance_uid,
        "series_instance_uid": series.series_instance_uid,
        "sop_instance_uid": image.sop_instance_uid,
        "instance_id": image.id,
    }


@router.post(
    "/{source_message_id}/failure",
    response={
        200: StatusResponse,
        403: StatusResponse,
        404: ErrorResponse,
    },
)
def report_failure(request, source_message_id: str, payload: FailurePayload):
    """
    Report a C-STORE validation failure for a gateway action.
    """
    try:
        action = GatewayAction.objects.get(id=source_message_id)
    except (GatewayAction.DoesNotExist, ValueError):
        return 404, {
            "title": "Not Found",
            "status": 404,
            "detail": f"GatewayAction {source_message_id!r} not found.",
        }

    action.status = GatewayActionStatus.IMAGE_FAILED
    action.last_error = payload.error
    action.failed_at = timezone.now()
    action.save(update_fields=["status", "last_error", "failed_at", "updated_at"])

    return 200, {"status": "failure recorded"}
