from django.contrib.postgres.fields import ArrayField
from django.core.files.storage import storages
from django.db import models


def dicom_storage():
    return storages["dicom"]


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


class Study(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["study_instance_uid"]),
            models.Index(fields=["patient_id"]),
            models.Index(fields=["source_message_id"]),
        ]

    study_instance_uid = models.CharField(max_length=128, unique=True)
    source_message_id = models.CharField(max_length=128)
    patient_id = models.CharField(max_length=10, blank=True)
    date_and_time = models.DateTimeField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)

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

    def __str__(self):
        return self.study_instance_uid


class Series(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["series_instance_uid"]),
        ]

    series_instance_uid = models.CharField(max_length=128, unique=True)
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="series")
    modality = models.CharField(max_length=16, blank=True)
    series_number = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.series_instance_uid


class Image(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["sop_instance_uid"]),
        ]

    sop_instance_uid = models.CharField(max_length=128, unique=True)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name="images")
    instance_number = models.IntegerField(null=True, blank=True)
    dicom_file = models.FileField(storage=dicom_storage)
    image_file = models.FileField(storage=dicom_storage, null=True, blank=True)
    laterality = models.CharField(max_length=16, blank=True)
    view_position = models.CharField(max_length=16, blank=True)

    def laterality_and_view(self):
        if self.laterality and self.view_position:
            return f"{self.laterality}{self.view_position}".upper()
        return None

    def __str__(self):
        return self.sop_instance_uid
