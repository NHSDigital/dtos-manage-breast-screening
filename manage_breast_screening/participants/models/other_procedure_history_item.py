from django.db import models

from ...core.models import BaseModel
from .appointment import Appointment


class OtherProcedureHistoryItem(BaseModel):
    class Procedure(models.TextChoices):
        BREAST_REDUCTION = "BREAST_REDUCTION", "Breast reduction"
        BREAST_SYMMETRISATION = "BREAST_SYMMETRISATION", "Breast symmetrisation"
        NIPPLE_CORRECTION = "NIPPLE_CORRECTION", "Nipple correction"
        OTHER = "OTHER", "Other"

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="other_procedure_history_items",
    )
    procedure = models.CharField(choices=Procedure)
    procedure_details = models.CharField(blank=True, null=False, default="")
    procedure_year = models.IntegerField(null=True)
    additional_details = models.TextField(blank=True, null=False, default="")
