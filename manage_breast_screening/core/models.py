import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class BaseModel(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Automatically trim whitespace from any text fields
        """
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if value:
                    setattr(self, field.name, value.strip())


class AuditLog(models.Model):
    class Operations:
        CREATE = "create"
        UPDATE = "update"
        DELETE = "delete"

    OperationChoices = [
        (Operations.CREATE, "Create"),
        (Operations.UPDATE, "Update"),
        (Operations.DELETE, "Delete"),
    ]

    class Meta:
        indexes = [
            models.Index(fields=["content_type_id", "object_id", "created_at"]),
            models.Index(fields=["system_update_id", "created_at"]),
            models.Index(fields=["actor_id", "created_at"]),
        ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, null=True)
    object_id = models.UUIDField()
    operation = models.CharField(choices=OperationChoices)
    snapshot = models.JSONField(encoder=DjangoJSONEncoder)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True
    )
    system_update_id = models.CharField(null=True)

    def __str__(self):
        return f"{self.get_operation_display()} {self.content_type} ({self.object_id})"
