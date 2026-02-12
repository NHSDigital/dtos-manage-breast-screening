from dataclasses import dataclass

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Value, When
from typing_extensions import Literal

from manage_breast_screening.core.models import BaseModel


@dataclass(frozen=True)
class ImageView:
    view_position: Literal["CC", "MLO", "EKLUND"]
    laterality: Literal["R", "L"]

    @classmethod
    def from_short_name(cls, short_name):
        match short_name:
            case "RCC":
                return cls("CC", "R")
            case "RMLO":
                return cls("MLO", "R")
            case "Right Eklund":
                return cls("EKLUND", "R")
            case "LCC":
                return cls("CC", "L")
            case "LMLO":
                return cls("MLO", "L")
            case "Left Eklund":
                return cls("EKLUND", "L")
            case _:
                raise ValueError(short_name)

    @property
    def short_name(self):
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


ALL_VIEWS_RCC_FIRST = [
    ImageView.from_short_name(name)
    for name in ["RCC", "RMLO", "Right Eklund", "LCC", "LMLO", "Left Eklund"]
]
EKLUND_VIEWS = [ImageView("EKLUND", "R"), ImageView("EKLUND", "L")]


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


class RepeatReason(models.TextChoices):
    PATIENT_MOVED = "PATIENT_MOVED", "Patient moved during exposure"
    UNABLE_COMPRESSION = "UNABLE_COMPRESSION", "Unable to maintain compression"
    INADEQUATE_COMPRESSION = (
        "INADEQUATE_COMPRESSION",
        "Inadequate compression achieved",
    )
    INCORRECT_POSITIONING = (
        "INCORRECT_POSITIONING",
        "Incorrect positioning identified",
    )
    IMAGE_TOO_LIGHT = "IMAGE_TOO_LIGHT", "Image too light - exposure needs adjustment"
    IMAGE_TOO_DARK = "IMAGE_TOO_DARK", "Image too dark - exposure needs adjustment"
    MOTION_BLUR = "MOTION_BLUR", "Motion blur affecting image quality"
    EQUIPMENT_FAULT = "EQUIPMENT_FAULT", "Equipment technical fault"
    FOLDED_SKIN = "FOLDED_SKIN", "Folded skin needs smoothing"
    PECTORAL_MUSCLE = "PECTORAL_MUSCLE", "Pectoral muscle not visualised correctly"
    OTHER = "OTHER", "Other"


class RepeatType(models.TextChoices):
    ALL_REPEATS = "ALL_REPEATS", "All additional images were repeats"
    SOME_REPEATS = "SOME_REPEATS", "Some were repeats, some were extra images"
    NO_REPEATS = "NO_REPEATS", "No repeats - all extra images were needed"


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

    def has_series_with_multiple_images(self):
        return self.series_with_multiple_images().exists()

    def series_with_multiple_images(self):
        return self.series_set.filter(count__gt=1).order_rcc_first()

    def series_counts(self):
        # Initialise everything with 0 so missing series are included
        # and the order is respected.
        counts = {view: 0 for view in ALL_VIEWS_RCC_FIRST}

        for view_position, laterality, count in self.series_set.values_list(
            "view_position", "laterality", "count"
        ):
            view = ImageView(view_position, laterality)
            counts[view] = count

        return counts


class SeriesQuerySet(models.QuerySet):
    def order_rcc_first(self):
        return self.order_by(
            "-laterality",
            Case(
                When(view_position="CC", then=Value(0)),
                When(view_position="MLO", then=Value(1)),
                When(view_position="EKLUND", then=Value(2)),
            ),
        )


class Series(BaseModel):
    objects = SeriesQuerySet.as_manager()

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

    repeat_type = models.CharField(
        max_length=20, choices=RepeatType.choices, blank=True, null=True
    )
    repeat_count = models.PositiveSmallIntegerField(blank=True, null=True)
    repeat_reasons = ArrayField(
        base_field=models.CharField(max_length=30, choices=RepeatReason.choices),
        default=list,
        blank=True,
    )

    class Meta:
        unique_together = ["study", "view_position", "laterality"]

    def __str__(self):
        return ImageView(self.view_position, self.laterality).short_name
