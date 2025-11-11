from django.contrib.postgres.fields import ArrayField
from django.db import models

from ...core.models import BaseModel
from .appointment import Appointment


class MastectomyOrLumpectomyHistoryItem(BaseModel):
    class Procedure(models.TextChoices):
        LUMPECTOMY = "LUMPECTOMY", "Lumpectomy"
        MASTECTOMY_TISSUE_REMAINING = (
            "MASTECTOMY_TISSUE_REMAINING",
            "Mastectomy (tissue remaining)",
        )
        MASTECTOMY_NO_TISSUE_REMAINING = (
            "MASTECTOMY_NO_TISSUE_REMAINING",
            "Mastectomy (no tissue remaining)",
        )
        NO_PROCEDURE = "NO_PROCEDURE", "No procedure"

    class Surgery(models.TextChoices):
        RECONSTRUCTION = "RECONSTRUCTION", "Reconstruction"
        SYMMETRISATION = "SYMMETRISATION", "Symmetrisation"
        NO_SURGERY = "NO_SURGERY", "No surgery"

    class SurgeryReason(models.TextChoices):
        RISK_REDUCTION = "RISK_REDUCTION", "Risk reduction"
        GENDER_AFFIRMATION = "GENDER_AFFIRMATION", "Gender-affirmation (top surgery)"
        OTHER_REASON = "OTHER_REASON", "Other reason"

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="mastectomy_or_lumpectomy_history_items",
    )
    right_breast_procedure = models.CharField(choices=Procedure)
    left_breast_procedure = models.CharField(choices=Procedure)
    right_breast_other_surgery = ArrayField(
        base_field=models.CharField(choices=Surgery),
        default=list,
    )
    left_breast_other_surgery = ArrayField(
        base_field=models.CharField(choices=Surgery),
        default=list,
    )
    year_of_surgery = models.IntegerField(null=True, blank=True)
    surgery_reason = models.CharField(choices=SurgeryReason)
    additional_details = models.TextField(blank=True, null=False, default="")
