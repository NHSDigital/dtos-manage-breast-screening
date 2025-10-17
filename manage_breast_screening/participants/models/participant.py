import uuid
from datetime import date

from django.contrib.postgres.fields import ArrayField
from django.db import models

from ...core.models import BaseModel
from .appointment import Appointment
from .ethnicity import Ethnicity


class Participant(BaseModel):
    PREFER_NOT_TO_SAY = "Prefer not to say"
    ETHNIC_BACKGROUND_CHOICES = Ethnicity.ethnic_background_ids_with_display_names()

    first_name = models.TextField()
    last_name = models.TextField()
    gender = models.TextField()
    nhs_number = models.TextField()
    phone = models.TextField()
    email = models.EmailField()
    date_of_birth = models.DateField()
    ethnic_background_id = models.CharField(
        blank=True, null=True, choices=ETHNIC_BACKGROUND_CHOICES
    )
    any_other_background_details = models.TextField(blank=True, null=True)
    risk_level = models.TextField()
    extra_needs = models.JSONField(null=False, default=list, blank=True)

    @property
    def appointments(self):
        return Appointment.objects.filter(screening_episode__participant=self)

    @property
    def full_name(self):
        return " ".join([name for name in [self.first_name, self.last_name] if name])

    def age(self):
        today = date.today()
        if (today.month, today.day) >= (
            self.date_of_birth.month,
            self.date_of_birth.day,
        ):
            return today.year - self.date_of_birth.year
        else:
            return today.year - self.date_of_birth.year - 1

    @property
    def ethnic_category(self):
        return Ethnicity.ethnic_category(self.ethnic_background_id)

    @property
    def ethnic_background(self):
        if (
            self.ethnic_background_id in Ethnicity.non_specific_ethnic_backgrounds()
            and self.any_other_background_details
        ):
            return self.any_other_background_details
        else:
            return Ethnicity.ethnic_background_display_name(self.ethnic_background_id)


class ParticipantAddress(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    participant = models.OneToOneField(
        "participants.Participant", on_delete=models.PROTECT, related_name="address"
    )
    lines = ArrayField(models.CharField(), size=5, blank=True)
    postcode = models.CharField(blank=True, null=True)
