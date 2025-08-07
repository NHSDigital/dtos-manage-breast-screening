import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from manage_breast_screening.notifications.services.queue import Queue
from manage_breast_screening.notifications.validators.request_validator import (
    RequestValidator,
)


@require_http_methods(["POST"])
def create_message_status(request):
    valid, message = RequestValidator(request).valid()

    if not valid:
        logging.error("Request validation failed: %s", message)
        return JsonResponse({"error": {"message": message}}, status=400)

    Queue.MessageStatusUpdates().add(request.body.decode("ASCII"))

    return JsonResponse(
        {"result": {"message": "Message status update queued"}}, status=200
    )
