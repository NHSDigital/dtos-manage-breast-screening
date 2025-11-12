from django.contrib.postgres.fields import ArrayField
from django.db import models

from ...core.models import BaseModel
from .appointment import Appointment


class BenignLumpHistoryItem(BaseModel):
    class Procedure(models.TextChoices):
        NEEDLE_BIOPSY = "NEEDLE_BIOPSY", "Needle biopsy"
        LUMP_REMOVED = "LUMP_REMOVED", "Lump removed"
        NO_PROCEDURES = "NO_PROCEDURES", "No procedures"

    class ProcedureLocation(models.TextChoices):
        NHS_HOSPITAL = "NHS_HOSPITAL", "At an NHS hospital"
        PRIVATE_CLINIC_UK = "PRIVATE_CLINIC_UK", "At a private clinic in the UK"
        OUTSIDE_UK = "OUTSIDE_UK", "Outside the UK"
        MULTIPLE_LOCATIONS = "MULTIPLE_LOCATIONS", "In multiple locations"
        EXACT_LOCATION_UNKNOWN = "EXACT_LOCATION_UNKNOWN", "Exact location unknown"

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="benign_lump_history_items",
    )
    right_breast_procedures = ArrayField(
        base_field=models.CharField(choices=Procedure),
        default=list,
    )
    left_breast_procedures = ArrayField(
        base_field=models.CharField(choices=Procedure),
        default=list,
    )
    procedure_year = models.IntegerField(null=True)
    procedure_location = models.CharField(choices=ProcedureLocation)
    procedure_location_details = models.CharField(blank=True, null=False, default="")
    additional_details = models.TextField(blank=True, null=False, default="")
