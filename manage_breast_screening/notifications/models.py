import uuid

from django.db import models

from ..core.models import BaseModel


class MessageBatchStatusChoices(models.Choices):
    FAILED_RECOVERABLE = "failed_recoverable"
    FAILED_UNRECOVERABLE = "failed_unrecoverable"
    SCHEDULED = "scheduled"
    SENT = "sent"
    UNSCHEDULED = "unscheduled"


class MessageStatusChoices(models.Choices):
    DELIVERED = "delivered"
    ENDRICHED = "enriched"
    FAILED = "failed"
    PENDING_ENRICHMENT = "pending_enrichment"
    SENDING = "sending"


class ChannelStatusChoices(models.Choices):
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    DELIVERED = "delivered"
    NOTIFICATION_ATTEMPTED = "notification_attempted"
    NOTIFIED = "notified"
    PENDING_VIRUS_CHECK = "pending_virus_check"
    READ = "read"
    RECEIVED = "received"
    REJECTED = "rejected"
    PERMANENT_FAILURE = "permanent_failure"
    TECHNICAL_FAILURE = "technical_failure"
    TEMPORARY_FAILURE = "temporary_failure"
    UNKNOWN = "unknown"
    UNNOTIFIED = "unnotified"
    VALIDATION_FAILED = "validation_failed"


class AppointmentStatusChoices(models.Choices):
    BOOKED = "B"
    CANCELLED = "C"
    UPDATED = "U"


class AppointmentEpisodeTypeChoices(models.Choices):
    EARLY_RECALL = "N"
    GP_REFERRAL = "G"
    ROUTINE_FIRST_CALL = "F"
    ROUTINE_RECALL = "R"
    SELF_REFERRAL = "S"
    VERY_HIGH_RISK = "H"
    VHR_SHORT_TERM_RECALL = "T"


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
        max_length=50, choices=MessageBatchStatusChoices, default="unscheduled"
    )
    nhs_notify_errors = models.JSONField(blank=True, null=True)

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
        max_length=50, choices=MessageStatusChoices, default="pending_enrichment"
    )

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
    batch_id = models.CharField(max_length=30, default="")
    nbss_id = models.CharField(max_length=30, unique=True)
    nhs_number = models.BigIntegerField(null=False)
    episode_type = models.CharField(
        max_length=30, choices=AppointmentEpisodeTypeChoices, default=""
    )
    episode_started_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=50, choices=AppointmentStatusChoices)
    booked_by = models.CharField(max_length=50)
    booked_at = models.DateTimeField(null=True)
    cancelled_by = models.CharField(max_length=50)
    cancelled_at = models.DateTimeField(null=True)
    number = models.IntegerField(null=True, default=1)
    starts_at = models.DateTimeField(null=False)
    created_at = models.DateTimeField(null=False, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    clinic = models.ForeignKey("notifications.Clinic", on_delete=models.PROTECT)

    def __str__(self):
        return f"Appointment for {self.starts_at} at {self.clinic}"


class Clinic(models.Model):
    """
    A clinic where an appointment is held.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    bso_code = models.CharField(max_length=50, null=True)
    name = models.CharField(max_length=50)
    alt_name = models.CharField(max_length=50)
    holding_clinic = models.BooleanField()
    location_code = models.CharField(max_length=50)
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


class ChannelStatus(models.Model):
    """
    A status update event for specific message communication channel
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey("notifications.Message", on_delete=models.PROTECT)
    channel = models.CharField(max_length=50, null=False)
    status = models.CharField(max_length=50, null=False, choices=ChannelStatusChoices)
    description = models.CharField(max_length=150)
    idempotency_key = models.CharField(max_length=150, unique=True)
    status_updated_at = models.DateTimeField(null=False)
    created_at = models.DateTimeField(null=False, auto_now_add=True)
    updated_at = models.DateTimeField(null=False, auto_now_add=True)


class MessageStatus(models.Model):
    """
    A status update event for a message
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey("notifications.Message", on_delete=models.PROTECT)
    status = models.CharField(max_length=50, null=False, choices=MessageStatusChoices)
    description = models.CharField(max_length=150)
    idempotency_key = models.CharField(max_length=150, unique=True)
    status_updated_at = models.DateTimeField(null=False)
    created_at = models.DateTimeField(null=False, auto_now_add=True)
    updated_at = models.DateTimeField(null=False, auto_now_add=True)
