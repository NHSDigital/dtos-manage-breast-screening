from django.db import models

from ...core.models import BaseModel
from .appointment import Appointment


class CystHistoryItem(BaseModel):
    class Treatment(models.TextChoices):
        DRAINAGE_OR_REMOVAL = "DRAINAGE_OR_REMOVAL", "Drainage or removal"
        NO_TREATMENT = "NO_TREATMENT", "No treatment"

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="cyst_history_items",
    )
    treatment = models.CharField(choices=Treatment)
    additional_details = models.TextField(blank=True, null=False, default="")
