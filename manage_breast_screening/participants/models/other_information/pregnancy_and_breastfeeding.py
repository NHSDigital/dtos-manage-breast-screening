from django.db import models

from ....core.models import BaseModel
from ..appointment import Appointment


class PregnancyAndBreastfeeding(BaseModel):
    class PregnancyStatus(models.TextChoices):
        YES = "YES", "Yes"
        NO_BUT_HAS_BEEN_RECENTLY = (
            "NO_BUT_HAS_BEEN_RECENTLY",
            "No, but has been recently",
        )
        NO = "NO", "No"

    class BreastfeedingStatus(models.TextChoices):
        YES = "YES", "Yes"
        NO_BUT_STOPPED_RECENTLY = "NO_BUT_STOPPED_RECENTLY", "No, but stopped recently"
        NO = "NO", "No"

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name="pregnancy_and_breastfeeding",
    )

    pregnancy_status = models.CharField(choices=PregnancyStatus)
    approx_pregnancy_due_date = models.CharField(blank=True, null=False, default="")
    approx_pregnancy_end_date = models.CharField(blank=True, null=False, default="")
    breastfeeding_status = models.CharField(choices=BreastfeedingStatus)
    approx_breastfeeding_start_date = models.CharField(
        blank=True, null=False, default=""
    )
    approx_breastfeeding_end_date = models.CharField(choices=BreastfeedingStatus)
