import pydicom
from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from manage_breast_screening.core.decorators import basic_auth_exempt

from .dicom_recorder import DicomRecorder


@login_not_required
@basic_auth_exempt
@csrf_exempt
@require_POST
def upload_dicom(request):
    """
    Accepts POST with a single DICOM file in form field 'file'
    """
    source_message_id = request.META.get("HTTP_X_SOURCE_MESSAGE_ID")
    if not source_message_id:
        return JsonResponse({"error": "Missing X-Source-Message-ID header"}, status=400)

    dicom_file = request.FILES.get("file")
    if dicom_file is None:
        return JsonResponse({"error": "No DICOM file provided"}, status=400)

    try:
        ds = pydicom.dcmread(dicom_file)
        records = DicomRecorder.create_records(source_message_id, ds, dicom_file)

    except pydicom.errors.InvalidDicomError:
        return JsonResponse({"error": "Invalid DICOM file"}, status=400)
    except AttributeError:
        return JsonResponse({"error": "Missing required DICOM UIDs"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)

    if not records:
        return JsonResponse({"error": "DICOM instance already exists"}, status=409)

    study, series, instance = records
    return JsonResponse(
        {
            "study_instance_uid": study.study_instance_uid,
            "series_instance_uid": series.series_instance_uid,
            "sop_instance_uid": instance.sop_instance_uid,
            "instance_id": instance.id,
        },
        status=201,
    )
