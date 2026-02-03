from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from manage_breast_screening.core.models import BaseModel


class StudyCompleteness(models.TextChoices):
    """
    A COMPLETE study is one where at least 1 image is taken
    for each of the 4 standard views.

    A study is PARTIAL if it is missing images for 1 or more views,
    but the study is considered done. There is a reason for not
    taking a full set, that cannot be addressed by recalling
    the participant for another appointment.

    A study is INCOMPLETE if the full set couldn't be taken,
    but the reason is temporary, and the participant could
    be invited back to complete the set.
    """

    COMPLETE = "COMPLETE", "Complete set of images"
    PARTIAL = "PARTIAL", "Partial mammography"
    INCOMPLETE = "INCOMPLETE", "Incomplete set of images"


class IncompleteImagesReason(models.TextChoices):
    CONSENT_WITHDRAWN = "CONSENT_WITHDRAWN", "Consent withdrawn"
    LANGUAGE_OR_LEARNING_DIFFICULTIES = (
        "LANGUAGE_OR_LEARNING_DIFFICULTIES",
        "Language or learning difficulties",
    )
    UNABLE_TO_SCAN_TISSUE = "UNABLE_TO_SCAN_TISSUE", "Unable to scan tissue"
    WHEELCHAIR = "WHEELCHAIR", "Positioning difficulties due to wheelchair"
    OTHER_MOBILITY = (
        "OTHER_MOBILITY",
        "Positioning difficulties for other mobility reasons",
    )
    TECHNICAL_ISSUES = "TECHNICAL_ISSUES", "Technical issues"
    OTHER = "OTHER", "Other"


class Study(BaseModel):
    appointment = models.OneToOneField(
        "participants.Appointment", on_delete=models.PROTECT
    )

    additional_details = models.TextField(blank=True, null=False, default="")
    imperfect_but_best_possible = models.BooleanField(default=False, null=False)
    completeness = models.CharField(
        choices=StudyCompleteness, blank=True, null=False, default=""
    )

    reasons_incomplete = ArrayField(
        base_field=models.CharField(
            choices=IncompleteImagesReason, blank=True, null=False, default=""
        ),
        default=list,
        null=False,
    )
    reasons_incomplete_details = models.TextField(blank=True, null=False, default="")


class Series(BaseModel):
    study = models.ForeignKey(Study, on_delete=models.PROTECT)

    view_position = models.CharField(
        max_length=10,
        blank=True,
        help_text="e.g., CC, MLO",
        choices=[("CC", "CC"), ("MLO", "MLO"), ("EKLUND", "EKLUND")],
    )
    laterality = models.CharField(
        max_length=1,
        blank=True,
        help_text="L or R",
        choices=[("L", "Left"), ("R", "Right")],
    )
    count = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )

    class Meta:
        unique_together = ["study", "view_position", "laterality"]

    def __str__(self):
        match (self.view_position, self.laterality):
            case ("CC", "R"):
                return "RCC"
            case ("MLO", "R"):
                return "RMLO"
            case ("EKLUND", "R"):
                return "Right Eklund"
            case ("CC", "L"):
                return "LCC"
            case ("MLO", "L"):
                return "LMLO"
            case ("EKLUND", "L"):
                return "Left Eklund"
            case _:
                return f"{self.view_position} {self.laterality}"
