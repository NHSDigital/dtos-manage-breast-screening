import json
from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.mammograms.forms.breast_feature_form import (
    CreateBreastFeatureForm,
    UpdateBreastFeatureForm,
)
from manage_breast_screening.participants.models.breast_features import (
    BreastFeatureAnnotation,
)


@pytest.mark.django_db
class TestCreateBreastFeatureForm:
    def test_saves_to_appointment(self, in_progress_appointment, clinical_user):
        json_obj = [{"arbitrary": "json"}]
        form = CreateBreastFeatureForm(
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

    def test_intiial(self, in_progress_appointment):
        form = CreateBreastFeatureForm(
            appointment=in_progress_appointment,
        )
        assert form["features"].initial == []

    def test_invalid_json(self, in_progress_appointment):
        form = CreateBreastFeatureForm(
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


@pytest.mark.django_db
class TestUpdateBreastFeatureForm:
    def test_saves_to_appointment(self, in_progress_appointment, clinical_user):
        BreastFeatureAnnotation.objects.create(
            annotations_json=[{"existing": "data"}], appointment=in_progress_appointment
        )

        json_obj = [{"arbitrary": "json"}]
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
        BreastFeatureAnnotation.objects.create(
            annotations_json={"existing": "data"}, appointment=in_progress_appointment
        )
        form = UpdateBreastFeatureForm(
            appointment=in_progress_appointment,
        )
        assert form["features"].initial == {"existing": "data"}
