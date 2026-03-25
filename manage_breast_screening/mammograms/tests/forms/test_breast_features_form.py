import json
from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.mammograms.forms.breast_feature_form import (
    AddBreastFeatureForm,
    UpdateBreastFeatureForm,
)
from manage_breast_screening.participants.models.breast_features import (
    BreastFeatureAnnotation,
)


@pytest.mark.django_db
class TestCreateBreastFeatureForm:
    def test_saves_to_appointment(self, in_progress_appointment, clinical_user):
        json_obj = [{"id": "mole", "region_id": "def", "x": 1, "y": 2}]
        form = AddBreastFeatureForm(
            QueryDict(
                urlencode(
                    {
                        "features": json.dumps(json_obj),
                    },
                    doseq=True,
                )
            ),
            appointment=in_progress_appointment,
        )

        assert form.is_valid()
        instance = form.save(clinical_user)
        assert instance.diagram_version == 1
        assert instance.appointment == in_progress_appointment
        assert instance.annotations_json == json_obj

    def test_intitial(self, in_progress_appointment):
        form = AddBreastFeatureForm(
            appointment=in_progress_appointment,
        )
        assert form["features"].initial == []

    def test_malformed_json(self, in_progress_appointment):
        form = AddBreastFeatureForm(
            QueryDict(
                urlencode(
                    {
                        "features": "bad",
                    },
                    doseq=True,
                )
            ),
            appointment=in_progress_appointment,
        )

        assert not form.is_valid()
        assert form.errors == {
            "features": ["There was a problem saving the annotations"]
        }

    def test_invalid_json(self, in_progress_appointment):
        form = AddBreastFeatureForm(
            QueryDict(
                urlencode(
                    {
                        "features": '[{"region_id": "abc"}]',
                    },
                    doseq=True,
                )
            ),
            appointment=in_progress_appointment,
        )

        assert not form.is_valid()
        assert form.errors == {
            "features": ["There was a problem saving the annotations"]
        }

    def test_pending_feature_id(self, in_progress_appointment):
        form = AddBreastFeatureForm(
            QueryDict(
                urlencode(
                    {
                        "features": '[{"region_id": "abc", "id": "pending", "x": 1, "y": 1}]',
                    },
                    doseq=True,
                )
            ),
            appointment=in_progress_appointment,
        )

        assert not form.is_valid()
        assert form.errors == {"features": ["Select a feature type"]}


@pytest.mark.django_db
class TestUpdateBreastFeatureForm:
    def test_saves_to_appointment(self, in_progress_appointment, clinical_user):
        BreastFeatureAnnotation.objects.create(
            annotations_json=[{"id": "mole", "region_id": "features", "x": 0, "y": 0}],
            appointment=in_progress_appointment,
        )

        json_obj = [{"id": "scar", "region_id": "def", "x": 1, "y": 2}]
        form = UpdateBreastFeatureForm(
            QueryDict(
                urlencode(
                    {
                        "features": json.dumps(json_obj),
                    },
                    doseq=True,
                )
            ),
            appointment=in_progress_appointment,
        )

        assert form.is_valid()
        instance = form.save(clinical_user)
        assert instance.diagram_version == 1
        assert instance.appointment == in_progress_appointment
        assert instance.annotations_json == json_obj

    def test_populates_initial_data(self, in_progress_appointment):
        initial_features = [{"id": "mole", "region_id": "def", "x": 1, "y": 2}]
        BreastFeatureAnnotation.objects.create(
            annotations_json=initial_features,
            appointment=in_progress_appointment,
        )
        form = UpdateBreastFeatureForm(
            appointment=in_progress_appointment,
        )
        assert form["features"].initial == initial_features
