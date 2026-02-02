from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from manage_breast_screening.core.models import BaseModel


class Study(BaseModel):
    appointment = models.OneToOneField(
        "participants.Appointment", on_delete=models.PROTECT
    )

    additional_details = models.TextField(blank=True, null=False, default="")


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
