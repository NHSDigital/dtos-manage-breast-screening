from django.db import models

from ...core.models import BaseModel


class ConfirmedPreviousMammogram(BaseModel):
    participant = models.ForeignKey(
        "participants.Participant",
        on_delete=models.PROTECT,
        related_name="confirmed_previous_mammograms",
    )
    location_details = models.TextField(null=False, default="", blank=True)
    exact_date = models.DateField(null=False, blank=False)
