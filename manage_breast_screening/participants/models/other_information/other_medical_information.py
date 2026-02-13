from django.db import models

from ....core.models import BaseModel
from ..appointment import Appointment


class OtherMedicalInformation(BaseModel):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name="other_medical_information",
    )
    details = models.TextField(blank=True)
