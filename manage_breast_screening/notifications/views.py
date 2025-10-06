import logging

from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from manage_breast_screening.core.decorators import (
    basic_auth_exempt,
)
from manage_breast_screening.notifications.services.queue import Queue
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
        logging.error("Request validation failed: %s", message)
        return JsonResponse({"error": {"message": message}}, status=400)

    Queue.MessageStatusUpdates().add(request.body.decode("ASCII"))

    return JsonResponse(
        {"result": {"message": "Message status update queued"}}, status=200
    )
