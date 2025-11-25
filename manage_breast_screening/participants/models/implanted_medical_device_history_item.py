from django.db import models

from ...core.models import BaseModel
from .appointment import Appointment


class ImplantedMedicalDeviceHistoryItem(BaseModel):
    class Device(models.TextChoices):
        CARDIAC_DEVICE = "CARDIAC_DEVICE", "Cardiac device (such as a pacemaker or ICD)"
        HICKMAN_LINE = "HICKMAN_LINE", "Hickman line"
        OTHER_MEDICAL_DEVICE = (
            "OTHER_MEDICAL_DEVICE",
            "Other medical device (or does not know)",
        )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="implanted_medical_device_history_items",
    )
    device = models.CharField(choices=Device)
    other_medical_device_details = models.CharField(blank=True, null=False, default="")
    procedure_year = models.IntegerField(null=True)
    device_has_been_removed = models.BooleanField()
    removal_year = models.IntegerField(null=True)
    additional_details = models.TextField(blank=True, null=False, default="")
