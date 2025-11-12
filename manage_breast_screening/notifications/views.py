from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from manage_breast_screening.core.decorators import (
    basic_auth_exempt,
)
from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)
from manage_breast_screening.notifications.services.queue import (
    Queue,
    QueueConfigurationError,
)
from manage_breast_screening.notifications.validators.request_validator import (
    RequestValidator,
)


@require_http_methods(["POST"])
@login_not_required
@basic_auth_exempt
@csrf_exempt
def create_message_status(request):
    valid, message = RequestValidator(request).valid()

    if not valid:
        ApplicationInsightsLogging().custom_event(
            message=message,
            event_name="create_message_status_validation_error",
        )
        return JsonResponse({"error": {"message": message}}, status=400)

    try:
        Queue.MessageStatusUpdates().add(request.body.decode("ASCII"))

    except QueueConfigurationError as e:
        error_msg = "Queue service not configured. Check QUEUE_STORAGE_CONNECTION_STRING or STORAGE_ACCOUNT_NAME/QUEUE_MI_CLIENT_ID environment variables."
        ApplicationInsightsLogging().exception(f"Queue configuration error: {e}")
        return JsonResponse({"error": {"message": error_msg}}, status=500)

    except Exception as e:
        error_msg = f"Failed to queue message status update: {str(e)}"
        ApplicationInsightsLogging().exception(error_msg)
        return JsonResponse(
            {"error": {"message": "Internal server error processing request"}},
            status=500,
        )

    return JsonResponse(
        {"result": {"message": "Message status update queued"}}, status=200
    )
