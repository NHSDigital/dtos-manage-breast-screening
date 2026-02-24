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
        json_obj = [{"id": "abc", "name": "def", "x": 1, "y": 2}]
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
                        "features": '[{"name": "abc"}]',
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


@pytest.mark.django_db
class TestUpdateBreastFeatureForm:
    def test_saves_to_appointment(self, in_progress_appointment, clinical_user):
        BreastFeatureAnnotation.objects.create(
            annotations_json=[{"id": "existing", "name": "features", "x": 0, "y": 0}],
            appointment=in_progress_appointment,
        )

        json_obj = [{"id": "abc", "name": "def", "x": 1, "y": 2}]
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
        initial_features = [{"id": "abc", "name": "def", "x": 1, "y": 2}]
        BreastFeatureAnnotation.objects.create(
            annotations_json=initial_features,
            appointment=in_progress_appointment,
        )
        form = UpdateBreastFeatureForm(
            appointment=in_progress_appointment,
        )
        assert form["features"].initial == initial_features
