from django.db import models

from ....core.models import BaseModel
from ..appointment import Appointment


class HormoneReplacementTherapy(BaseModel):
    class Status(models.TextChoices):
        YES = "YES", "Yes"
        NO_BUT_STOPPED_RECENTLY = "NO_BUT_STOPPED_RECENTLY", "No, but stopped recently"
        NO = "NO", "No"

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name="hormone_replacement_therapy",
    )

    status = models.CharField(choices=Status)
    approx_start_date = models.CharField(blank=True, null=False, default="")
    approx_end_date = models.CharField(blank=True, null=False, default="")
    approx_previous_duration = models.CharField(blank=True, null=False, default="")
