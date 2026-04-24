from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def show_reading_dashboard(request):
    return render(request, "show_readings.jinja")
