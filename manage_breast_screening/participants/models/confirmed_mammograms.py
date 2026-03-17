from django.db import models

from manage_breast_screening.participants.models.appointment import Appointment

from ...core.models import BaseModel


class ConfirmedPreviousMammogram(BaseModel):
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="confirmed_mammograms",
    )
    provider = models.ForeignKey(
        "clinics.Provider", on_delete=models.PROTECT, null=True, blank=True
    )
    location_details = models.TextField(null=False, default="", blank=True)
    exact_date = models.DateField(null=True, blank=True)
