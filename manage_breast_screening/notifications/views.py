from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
def create_message_status(request):
    raise Exception("test create exception")
    # valid, message = RequestValidator(request).valid()

    # if not valid:
    #     logging.error("Request validation failed: %s", message)
    #     return JsonResponse({"error": {"message": message}}, status=400)

    # Queue.MessageStatusUpdates().add(request.body.decode("ASCII"))

    # return JsonResponse(
    #     {"result": {"message": "Message status update queued"}}, status=200
    # )
