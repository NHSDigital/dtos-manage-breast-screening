from django.contrib.postgres.fields import ArrayField
from django.db import models

from manage_breast_screening.core.models import BaseModel
from manage_breast_screening.participants.models.appointment import Appointment


class BreastAugmentationHistoryItem(BaseModel):
    """
    Details of breast implants or other augmentations
    """

    class Procedure(models.TextChoices):
        BREAST_IMPLANTS = ("BREAST_IMPLANTS", "Breast implants (silicone or saline)")
        OTHER_AUGMENTATION = ("OTHER_AUGMENTATION", "Other augmentation")
        NO_PROCEDURES = ("NO_PROCEDURES", "No procedures")

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="breast_augmentation_history_items",
    )
    right_breast_procedures = ArrayField(
        base_field=models.CharField(choices=Procedure), default=list
    )
    left_breast_procedures = ArrayField(
        base_field=models.CharField(choices=Procedure), default=list
    )
    procedure_year = models.IntegerField(null=True)
    implants_have_been_removed = models.BooleanField(default=False)
    removal_year = models.IntegerField(null=True)
    additional_details = models.TextField(null=False, blank=True, default="")
