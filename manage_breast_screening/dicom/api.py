import os
from typing import Any, Callable

import ninja
import pydicom
from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, HttpResponseBase

from manage_breast_screening.core.decorators import basic_auth_exempt

from .dicom_recorder import DicomRecorder


def get_view(self) -> Callable:
    if self.is_async:

        async def async_view_wrapper(
            request: HttpRequest, *args: Any, **kwargs: Any
        ) -> HttpResponseBase:
            return await self._async_view(request, *args, **kwargs)

        async_view_wrapper.csrf_exempt = True  # type: ignore
        async_view_wrapper = login_not_required(async_view_wrapper)  # type: ignore
        async_view_wrapper = basic_auth_exempt(async_view_wrapper)

        return async_view_wrapper
    else:

        def sync_view_wrapper(
            request: HttpRequest, *args: Any, **kwargs: Any
        ) -> HttpResponseBase:
            return self._sync_view(request, *args, **kwargs)

        sync_view_wrapper.csrf_exempt = True  # type: ignore
        sync_view_wrapper = login_not_required(sync_view_wrapper)  # type: ignore
        sync_view_wrapper = basic_auth_exempt(sync_view_wrapper)

        return sync_view_wrapper  # type: ignore


router = ninja.Router(auth=None)

ninja.operation.PathView.get_view = get_view


@router.get("/status")
def status(request):
    return 200, {"status": "API is running"}


@router.put("/upload")
def upload(request):
    """
    Accepts POST with a single DICOM file in form field 'file'
    """
    if not os.getenv("DICOM_API_ENABLED", "true").lower() == "true":
        return 403, {"error": "DICOM API is disabled"}

    source_message_id = request.META.get("HTTP_X_SOURCE_MESSAGE_ID")
    if not source_message_id:
        return 400, {"error": "Missing X-Source-Message-ID header"}

    dicom_file = request.FILES.get("file")
    if dicom_file is None:
        return 400, {"error": "No DICOM file provided"}

    try:
        records = DicomRecorder.create_records(source_message_id, dicom_file)

    except pydicom.errors.InvalidDicomError:
        return 400, {"error": "Invalid DICOM file"}
    except AttributeError:
        return 400, {"error": "Missing required DICOM UIDs"}
    except Exception as e:
        return 500, {"error": f"An error occurred: {e}"}

    study, series, instance = records

    return 201, {
        "study_instance_uid": study.study_instance_uid,
        "series_instance_uid": series.series_instance_uid,
        "sop_instance_uid": instance.sop_instance_uid,
        "instance_id": instance.id,
    }
