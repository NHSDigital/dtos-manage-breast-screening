from django.core.files.storage import storages
from django.db import models


def dicom_storage():
    return storages["dicom"]


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

    def __str__(self):
        return self.study_instance_uid


class Series(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["series_instance_uid"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["series_number", "study"],
                name="unique_series_number_per_study",
            )
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
        constraints = [
            models.UniqueConstraint(
                fields=["instance_number", "series"],
                name="unique_instance_number_per_series",
            )
        ]

    sop_instance_uid = models.CharField(max_length=128, unique=True)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name="images")
    instance_number = models.IntegerField(null=True, blank=True)
    dicom_file = models.FileField(storage=dicom_storage)

    def __str__(self):
        return self.sop_instance_uid
