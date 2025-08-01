import uuid

from django.db import models

from ..core.models import BaseModel

BATCH_STATUSES = [
    ("unscheduled", "Unscheduled"),
    ("scheduled", "Scheduled"),
    ("sent", "Sent"),
    ("failed", "Failed"),
]

MESSAGE_STATUSES = [
    ("pending_enrichment", "Pending enrichment"),
    ("enriched", "Enriched"),
    ("sending", "Sending"),
    ("delivered", "Delivered"),
    ("failed", "Failed"),
]


class MessageBatch(BaseModel):
    """
    Multiple messages sent as a batch
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notify_id = models.CharField(max_length=50, blank=True)
    routing_plan_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=BATCH_STATUSES, default="unscheduled"
    )

    def __str__(self):
        return f"MessageBatch {self.id} - Status: {self.status}"


class Message(models.Model):
    """
    A message sent to a participant.
    This is usually linked to a MessageBatch but can be a standalone message.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notify_id = models.CharField(max_length=50, blank=True)
    batch = models.ForeignKey(
        MessageBatch,
        related_name="messages",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=MESSAGE_STATUSES, default="pending_enrichment"
    )
    personalisation = models.JSONField(null=True)

    appointment = models.ForeignKey(
        "notifications.Appointment", on_delete=models.PROTECT
    )

    def __str__(self):
        return f"Message about {self.appointment} - Sent at: {self.sent_at}"


class Appointment(models.Model):
    """
    The screening appointment used to build the message.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nbss_id = models.CharField(max_length=30)
    nhs_number = models.BigIntegerField(null=False)
    status = models.CharField(max_length=50)
    booked_by = models.CharField(max_length=50)
    cancelled_by = models.CharField(max_length=50)
    number = models.IntegerField(null=True, default=1)
    starts_at = models.DateTimeField(null=False)
    created_at = models.DateTimeField(null=False, auto_now_add=True)

    clinic = models.ForeignKey("notifications.Clinic", on_delete=models.PROTECT)

    def __str__(self):
        return f"Appointment for {self.starts_at} at {self.clinic}"


class Clinic(models.Model):
    """
    A clinic where an appointment is held.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50)
    bso_code = models.CharField(max_length=50, null=True)
    name = models.CharField(max_length=50)
    alt_name = models.CharField(max_length=50)
    holding_clinic = models.BooleanField()
    location_code = models.CharField(max_length=50)
    address_description = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, null=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, null=True)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50)
    address_line_3 = models.CharField(max_length=50)
    address_line_4 = models.CharField(max_length=50)
    address_line_5 = models.CharField(max_length=50)
    address_line_5 = models.CharField(max_length=50)
    postcode = models.CharField(max_length=50)
    created_at = models.DateTimeField(null=False, auto_now_add=True)
    updated_at = models.DateTimeField(null=False, auto_now_add=True)

    def __str__(self):
        return f"Clinic {self.name} ({self.code})"
