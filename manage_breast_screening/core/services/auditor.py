from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers

from ..models import AuditLog


class AnonymousAuditError(ValueError):
    pass


class AuditAfterDeleteError(Exception):
    pass


def make_snapshot(obj):
    """
    Turn a model object into a python dictionary that can be stored in a JSON field
    """
    fields = [
        field.name
        for field in obj._meta.fields
        if field.name not in settings.AUDIT_EXCLUDED_FIELDS
    ]
    snapshot = serializers.serialize("python", [obj], fields=fields)[0]
    return snapshot["fields"]


def _log_action(object, operation, actor, system_update_id):
    """
    Create an audit record from a model instance
    """
    return AuditLog.objects.create(
        content_type=ContentType.objects.get_for_model(object),
        object_id=object.pk,
        operation=operation,
        snapshot=(
            {} if operation == AuditLog.Operations.DELETE else make_snapshot(object)
        ),
        actor=actor,
        system_update_id=system_update_id,
    )


def _log_actions(objects, operation, actor, system_update_id):
    """
    Create audit records from a queryset or list of model instances
    """
    log_entry_list = [
        AuditLog(
            content_type=ContentType.objects.get_for_model(object),
            object_id=object.pk,
            operation=operation,
            snapshot=(
                {} if operation == AuditLog.Operations.DELETE else make_snapshot(object)
            ),
            actor=actor,
            system_update_id=system_update_id,
        )
        for object in objects
    ]
    AuditLog.objects.bulk_create(log_entry_list)
    return log_entry_list


class Auditor:
    @classmethod
    def from_request(cls, request):
        return cls(request.user)

    def __init__(self, actor=None, system_update_id=None):
        self.actor = actor if actor and actor.is_authenticated else None
        self.system_update_id = system_update_id

        # Temporarily disable the requirement for a logged in user until we've implemented auth.
        # This should also consider non-production environments such as review apps.
        #
        # if self.actor is None and self.system_update_id is None:
        #     raise AnonymousAuditError(
        #         "Attempted to audit an operation with no logged in user and no system_update_id"
        #     )

    def audit_create(self, object) -> AuditLog:
        if object is None:
            raise TypeError("object must not be None")

        return _log_action(
            object,
            operation=AuditLog.Operations.CREATE,
            actor=self.actor,
            system_update_id=self.system_update_id,
        )

    def audit_update(self, object) -> AuditLog:
        if object is None:
            raise TypeError("object must not be None")

        return _log_action(
            object,
            operation=AuditLog.Operations.UPDATE,
            actor=self.actor,
            system_update_id=self.system_update_id,
        )

    def audit_delete(self, object) -> AuditLog:
        if object is None:
            raise TypeError("object must not be None")

        if object.pk is None:
            raise AuditAfterDeleteError(
                "Error auditing deletion of an unsaved object. Audit prior to deletion instead."
            )

        return _log_action(
            object,
            operation=AuditLog.Operations.DELETE,
            actor=self.actor,
            system_update_id=self.system_update_id,
        )

    def audit_bulk_create(self, objects) -> list[AuditLog]:
        return _log_actions(
            objects=objects,
            operation=AuditLog.Operations.CREATE,
            actor=self.actor,
            system_update_id=self.system_update_id,
        )

    def audit_bulk_update(self, objects) -> list[AuditLog]:
        return _log_actions(
            objects=objects,
            operation=AuditLog.Operations.UPDATE,
            actor=self.actor,
            system_update_id=self.system_update_id,
        )

    def audit_bulk_delete(self, objects) -> list[AuditLog]:
        return _log_actions(
            objects=objects,
            operation=AuditLog.Operations.DELETE,
            actor=self.actor,
            system_update_id=self.system_update_id,
        )
