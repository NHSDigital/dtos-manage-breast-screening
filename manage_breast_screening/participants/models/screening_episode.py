from django.db import models

from ...core.models import BaseModel


class ScreeningEpisode(BaseModel):
    class Protocol:
        FAMILY_HISTORY = "FAMILY_HISTORY"

    PROTOCOL_CHOICES = {
        Protocol.FAMILY_HISTORY: "Family history",
    }

    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.PROTECT
    )
    protocol = models.CharField(
        choices=PROTOCOL_CHOICES, default=Protocol.FAMILY_HISTORY, max_length=50
    )

    def screening_history(self):
        """
        Return all previous screening episodes, excluding this one, prefetching
        their appointment details as well.
        """
        return (
            ScreeningEpisode.objects.prefetch_related(
                "appointment_set__clinic_slot__clinic__setting__provider"
            )
            .filter(participant__pk=self.participant.pk)
            .exclude(pk=self.pk)
            .order_by("-created_at")
        )

    def previous(self) -> "ScreeningEpisode | None":
        """
        Return the last known screening episode
        """
        try:
            return self.screening_history()[0]
        except IndexError:
            return None
