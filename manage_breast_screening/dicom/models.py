import uuid

from django.contrib.postgres.fields import ArrayField
from django.core.files.storage import storages
from django.db import models

from manage_breast_screening.manual_images.models import (
    IncompleteImagesReason,
    RepeatReason,
    RepeatType,
    StudyCompleteness,
)


def dicom_storage():
    return storages["dicom"]


class Study(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["study_instance_uid"]),
            models.Index(fields=["patient_id"]),
            models.Index(fields=["source_message_id"]),
        ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
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

    def images(self) -> models.QuerySet["Image"]:
        return Image.objects.filter(series__study=self).order_by(
            "series__series_number", "instance_number"
        )

    @classmethod
    def for_appointment(cls, appointment):
        action = appointment.gateway_actions.first()
        if not action:
            return None

        return cls.objects.filter(source_message_id=action.id).first()

    def series_with_multiple_images(self):
        return self.series.annotate(image_count=models.Count("images")).filter(
            image_count__gt=1
        )

    def has_series_with_multiple_images(self):
        return self.series_with_multiple_images().exists()

    def __str__(self):
        return self.study_instance_uid


class Series(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["series_instance_uid"]),
        ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    series_instance_uid = models.CharField(max_length=128, unique=True)
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="series")
    modality = models.CharField(max_length=16, blank=True)
    series_number = models.IntegerField(null=True, blank=True)
    repeat_type = models.CharField(
        max_length=20, choices=RepeatType.choices, blank=True, null=True
    )
    repeat_count = models.PositiveSmallIntegerField(blank=True, null=True)
    repeat_reasons = ArrayField(
        base_field=models.CharField(max_length=30, choices=RepeatReason.choices),
        default=list,
        blank=True,
    )

    @property
    def count(self):
        return self.images.count()

    @property
    def extra_count(self):
        return self.images.filter(implant_present=True).count()

    @property
    def laterality(self):
        return self.images.first().laterality

    @property
    def view_position(self):
        return self.images.first().view_position

    def __str__(self):
        return str(self.images.first())


class Image(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["sop_instance_uid"]),
        ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    sop_instance_uid = models.CharField(max_length=128, unique=True)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name="images")
    instance_number = models.IntegerField(null=True, blank=True)
    dicom_file = models.FileField(storage=dicom_storage)
    image_file = models.FileField(storage=dicom_storage, null=True, blank=True)
    laterality = models.CharField(max_length=16, blank=True)
    view_position = models.CharField(max_length=16, blank=True)
    implant_present = models.BooleanField(default=False)

    @property
    def laterality_and_view(self):
        if self.laterality and self.view_position:
            return f"{self.laterality}{self.view_position}".upper()
        return ""

    def __str__(self):
        return self.laterality_and_view
