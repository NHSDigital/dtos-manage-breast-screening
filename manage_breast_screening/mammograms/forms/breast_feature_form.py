from logging import getLogger

import jsonschema
from django.forms import Form, HiddenInput, JSONField, ValidationError

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.participants.models.breast_features import (
    BreastFeatureAnnotation,
)

logger = getLogger(__name__)


class BreastFeatureForm(Form):
    VERSION = 1
    SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "x": {"type": "number"},
                "y": {"type": "number"},
            },
            "required": ["id", "name", "x", "y"],
            "additionalProperties": False,
        },
    }

    features = JSONField(
        widget=HiddenInput,
        required=True,
        initial=list,
        error_messages={
            "required": "Select one or more image features",
            "invalid": "There was a problem saving the annotations",
        },
    )

    def __init__(self, *args, appointment, **kwargs):
        self.appointment = appointment
        super().__init__(*args, **kwargs)

    def clean_features(self):
        data = self.cleaned_data["features"]

        try:
            jsonschema.validate(data, self.SCHEMA)
        except jsonschema.ValidationError as error:
            logger.exception(f"features JSON is not valid: {error.message}")
            raise ValidationError(
                message=self.fields["features"].error_messages["invalid"],
                code="invalid",
            )

        return data


class AddBreastFeatureForm(BreastFeatureForm):
    def save(self, current_user):
        instance = BreastFeatureAnnotation.objects.create(
            appointment=self.appointment,
            annotations_json=self.cleaned_data["features"],
            diagram_version=self.VERSION,
        )
        Auditor(current_user).audit_create(instance)

        return instance


class UpdateBreastFeatureForm(BreastFeatureForm):
    def __init__(self, *args, appointment, **kwargs):
        kwargs["initial"] = {"features": appointment.breast_features.annotations_json}

        super().__init__(*args, appointment=appointment, **kwargs)

    def save(self, current_user):
        instance = self.appointment.breast_features
        instance.annotations_json = self.cleaned_data["features"]
        instance.diagram_version = self.VERSION
        instance.save()
        Auditor(current_user).audit_update(instance)

        return instance
