from django.urls import path

from .views import upload_dicom

app_name = "dicom"

urlpatterns = [
    path("upload/", upload_dicom, name="dicom-upload"),
]
