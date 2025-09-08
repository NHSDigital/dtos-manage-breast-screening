from django.db import models

from ...core.models import BaseModel, ReferenceDataModel
from .appointment import Appointment
from .participant import Participant


class SymptomType(ReferenceDataModel):
    LUMP = "lump"
    SWELLING_OR_SHAPE_CHANGE = "swelling-or-shape-change"
    SKIN_CHANGE = "skin-change"
    NIPPLE_CHANGE = "nipple-change"
    OTHER = "other"

    name = models.CharField(null=False, blank=False)


class SymptomSubType(ReferenceDataModel):
    symptom_type = models.ForeignKey(SymptomType, on_delete=models.CASCADE)
    name = models.CharField(null=False, blank=False)


class SymptomAreas(models.TextChoices):
    RIGHT_BREAST = ("RIGHT_BREAST", "Right")
    LEFT_BREAST = ("LEFT_BREAST", "Left")
    BOTH_BREASTS = ("BOTH_BREASTS", "Both")
    OTHER = ("OTHER", "Other")


class Symptom(BaseModel):
    symptom_type = models.ForeignKey(SymptomType, on_delete=models.PROTECT)
    symptom_sub_type = models.ForeignKey(
        SymptomSubType, on_delete=models.PROTECT, null=True, blank=True
    )
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT)
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT)
    reported_at = models.DateField()

    # Optional further description of the symptom
    description = models.CharField(blank=True, null=False)

    # Whether the symptom is associated with the right/left breast
    area = models.CharField(choices=SymptomAreas, blank=False, null=False)
    area_description = models.CharField(blank=True, null=False)

    # Has the symptom been investigated already?
    investigated = models.BooleanField()

    # Onset information
    when_started = models.CharField(blank=True, null=False)
    year_started = models.IntegerField(null=True, blank=True)
    month_started = models.IntegerField(null=True, blank=True)
    intermittent = models.BooleanField(null=False, default=False)
    recently_resolved = models.BooleanField(null=False, default=False)
    when_resolved = models.CharField(blank=True, null=False)

    additional_information = models.CharField(blank=True, null=False)
