from django.contrib.postgres.fields import ArrayField
from django.db import models

from ...core.models import BaseModel
from .appointment import Appointment


class BreastCancerHistoryItem(BaseModel):
    class DiagnosisLocationChoices(models.TextChoices):
        RIGHT_BREAST = "RIGHT_BREAST", "Right breast"
        LEFT_BREAST = "LEFT_BREAST", "Left breast"
        BOTH_BREASTS = "BOTH_BREASTS", "Both breasts"
        DONT_KNOW = "DONT_KNOW", "Don't know"

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
        LYMPH_NODE_SURGERY = "LYMPH_NODE_SURGERY", "Lymph node surgery"
        RECONSTRUCTION = "RECONSTRUCTION", "Reconstruction"
        SYMMETRISATION = "SYMMETRISATION", "Symmetrisation"
        NO_SURGERY = "NO_SURGERY", "No surgery"

    class Treatment(models.TextChoices):
        BREAST_RADIOTHERAPY = "BREAST_RADIOTHERAPY", "Breast radiotherapy"
        LYMPH_NODE_RADIOTHERAPY = "LYMPH_NODE_RADIOTHERAPY", "Lymph node radiotherapy"
        NO_RADIOTHERAPY = "NO_RADIOTHERAPY", "No radiotherapy"

    class SystemicTreatment(models.TextChoices):
        CHEMOTHERAPY = "CHEMOTHERAPY", "Chemotherapy"
        HORMONE_THERAPY = "HORMONE_THERAPY", "Hormone therapy"
        OTHER = "OTHER", "Other"
        NO_SYSTEMIC_TREATMENTS = "NO_SYSTEMIC_TREATMENTS", "No systemic treatments"

    class InterventionLocation(models.TextChoices):
        NHS_HOSPITAL = "NHS_HOSPITAL", "At an NHS hospital"
        PRIVATE_CLINIC_UK = "PRIVATE_CLINIC_UK", "At a private clinic in the UK"
        OUTSIDE_UK = "OUTSIDE_UK", "Outside the UK"
        MULTIPLE_LOCATIONS = "MULTIPLE_LOCATIONS", "In multiple locations"
        EXACT_LOCATION_UNKNOWN = "EXACT_LOCATION_UNKNOWN", "Exact location unknown"

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="breast_cancer_history_items",
    )
    diagnosis_location = models.CharField(choices=DiagnosisLocationChoices)
    diagnosis_year = models.IntegerField(null=True)
    left_breast_procedure = models.CharField(choices=Procedure)
    right_breast_procedure = models.CharField(choices=Procedure)
    left_breast_other_surgery = ArrayField(
        base_field=models.CharField(choices=Surgery),
        default=list,
    )
    right_breast_other_surgery = ArrayField(
        base_field=models.CharField(choices=Surgery),
        default=list,
    )
    left_breast_treatment = ArrayField(
        base_field=models.CharField(choices=Treatment),
        default=list,
    )
    right_breast_treatment = ArrayField(
        base_field=models.CharField(choices=Treatment),
        default=list,
    )

    systemic_treatments = models.CharField(choices=SystemicTreatment)
    systemic_treatments_other_treatment_details = models.CharField(
        blank=True, null=False, default=""
    )

    intervention_location = models.CharField(choices=InterventionLocation)
    intervention_location_details = models.CharField(blank=True, null=False, default="")

    additional_details = models.TextField(blank=True, null=False, default="")
