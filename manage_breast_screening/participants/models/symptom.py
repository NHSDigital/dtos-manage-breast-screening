from django.db import models
from django.db.models import TextChoices

from ...core.models import BaseModel, ReferenceDataModel
from .appointment import Appointment


class SymptomType(ReferenceDataModel):
    LUMP = "LUMP"
    SWELLING_OR_SHAPE_CHANGE = "SWELLING_OR_SHAPE_CHANGE"
    SKIN_CHANGE = "SKIN_CHANGE"
    NIPPLE_CHANGE = "NIPPLE_CHANGE"
    OTHER = "OTHER"

    name = models.CharField(null=False, blank=False)


class SymptomSubType(ReferenceDataModel):
    symptom_type = models.ForeignKey(SymptomType, on_delete=models.CASCADE)
    name = models.CharField(null=False, blank=False)


class SkinChangeChoices(TextChoices):
    SORES_OR_CYSTS = "SORES_OR_CYSTS", "Sores or cysts"
    DIMPLES_OR_INDENTATION = (
        "DIMPLES_OR_INDENTATION",
        "Dimples or indentation",
    )
    RASH = "RASH", "Rash"
    COLOUR_CHANGE = "COLOUR_CHANGE", "Colour change"
    OTHER = "OTHER", "Other"


class SymptomAreas(models.TextChoices):
    RIGHT_BREAST = "RIGHT_BREAST", "Right breast"
    LEFT_BREAST = "LEFT_BREAST", "Left breast"
    BOTH_BREASTS = "BOTH_BREASTS", "Both breasts"
    OTHER = "OTHER", "Other"


class RelativeDateChoices(models.TextChoices):
    LESS_THAN_THREE_MONTHS = "LESS_THAN_THREE_MONTHS", "Less than 3 months"
    THREE_MONTHS_TO_A_YEAR = "THREE MONTHS TO A YEAR", "3 months to a year"
    ONE_TO_THREE_YEARS = "ONE_TO_THREE_YEARS", "1 to 3 years"
    OVER_THREE_YEARS = "OVER_THREE_YEARS", "Over 3 years"
    SINCE_A_SPECIFIC_DATE = "SINCE_A_SPECIFIC_DATE", "Since a specific date"
    NOT_SURE = "NOT_SURE", "Not sure"


class Symptom(BaseModel):
    symptom_type = models.ForeignKey(SymptomType, on_delete=models.PROTECT)
    symptom_sub_type = models.ForeignKey(
        SymptomSubType, on_delete=models.PROTECT, null=True, blank=True
    )
    symptom_sub_type_details = models.CharField(blank=True, null=False)

    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT)
    reported_at = models.DateField()

    # Optional further description of the symptom
    description = models.CharField(blank=True, null=False)

    # Whether the symptom is associated with the right/left breast
    area = models.CharField(choices=SymptomAreas, blank=False, null=False)
    area_description = models.CharField(blank=True, null=False)

    # Has the symptom been investigated already?
    investigated = models.BooleanField(null=False, default=False)
    investigation_details = models.CharField(blank=True, null=False)

    # Onset information
    when_started = models.CharField(blank=True, null=False, choices=RelativeDateChoices)
    year_started = models.IntegerField(null=True, blank=True)
    month_started = models.IntegerField(null=True, blank=True)
    intermittent = models.BooleanField(null=False, default=False)
    recently_resolved = models.BooleanField(null=False, default=False)
    when_resolved = models.CharField(blank=True, null=False)

    additional_information = models.CharField(blank=True, null=False)

    @property
    def participant(self):
        return self.appointment.participant
