import logging

from django.conf import settings
from django.db import models

from manage_breast_screening.core.models import BaseModel

logger = logging.getLogger(__name__)


class MedicalInformationSection(models.TextChoices):
    """
    The reviewable sections on the record medical information page.
    """

    MAMMOGRAM_HISTORY = "MAMMOGRAM_HISTORY", "Mammogram history"
    SYMPTOMS = "SYMPTOMS", "Symptoms"
    MEDICAL_HISTORY = "MEDICAL_HISTORY", "Medical history"
    BREAST_FEATURES = "BREAST_FEATURES", "Breast features"
    OTHER_INFORMATION = "OTHER_INFORMATION", "Other information"


class MedicalInformationReview(BaseModel):
    """
    Tracks whether a section of medical information has been reviewed
    for a specific appointment.
    """

    appointment = models.ForeignKey(
        "Appointment",
        on_delete=models.PROTECT,
        related_name="medical_information_reviews",
    )
    section = models.CharField(
        max_length=50,
        choices=MedicalInformationSection.choices,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        help_text="The user who marked this section as reviewed",
    )

    class Meta:
        unique_together = ("appointment", "section")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["appointment", "section"]),
        ]

    def __str__(self):
        return f"{self.get_section_display()} reviewed for appointment {self.appointment_id}"
