import os

from django.db import models
from django.utils.functional import cached_property

from manage_breast_screening.core.models import BaseModel


class GatewayActionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    CONFIRMED = "confirmed", "Confirmed"
    FAILED = "failed", "Failed"


class GatewayActionType(models.TextChoices):
    WORKLIST_CREATE = "worklist.create_item", "Create Worklist Item"


class GatewayAction(BaseModel):
    """Tracks actions sent to the screening gateway."""

    appointment = models.ForeignKey(
        "participants.Appointment",
        on_delete=models.PROTECT,
        related_name="gateway_actions",
    )
    type = models.CharField(max_length=50, choices=GatewayActionType.choices)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=GatewayActionStatus.choices,
        default=GatewayActionStatus.PENDING,
    )

    accession_number = models.CharField(max_length=100, unique=True, db_index=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    retry_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
        ]

    def __str__(self):
        return f"{self.type} - {self.accession_number} ({self.status})"


class Relay(BaseModel):
    provider = models.ForeignKey("clinics.Provider", on_delete=models.PROTECT)
    namespace = models.CharField(
        max_length=255,
        blank=True,
        help_text="Azure Relay namespace (e.g., myrelay.servicebus.windows.net)",
    )
    hybrid_connection_name = models.CharField(
        max_length=255, blank=True, help_text="Azure Relay hybrid connection name"
    )
    key_name = models.CharField(
        max_length=255, blank=True, help_text="Azure Relay shared access policy name"
    )
    shared_access_key_variable_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Environment variable name containing the shared access key",
    )

    @classmethod
    def for_provider(cls, provider):
        return cls.objects.filter(provider=provider).first()

    @cached_property
    def shared_access_key(self) -> str:
        return os.getenv(self.shared_access_key_variable_name, "")

    def __str__(self):
        return f"{self.id}"
