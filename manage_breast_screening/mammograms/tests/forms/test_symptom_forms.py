import pytest
from django.test import RequestFactory
from django.urls import reverse

from manage_breast_screening.forms.choices import YesNo
from manage_breast_screening.mammograms.forms.symptom_forms import (
    LumpForm,
    RightLeftOtherChoices,
    WhenStartedChoices,
)
from manage_breast_screening.participants.models.symptoms import (
    SymptomAreas,
    SymptomType,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


class TestLumpForm:
    def test_valid_form(self):
        form = LumpForm(
            data={
                "where_located": RightLeftOtherChoices.LEFT_BREAST,
                "how_long": WhenStartedChoices.LESS_THAN_THREE_MONTHS,
                "investigated": YesNo.NO,
            }
        )
        assert form.is_valid()

    def test_missing_required_fields(self):
        form = LumpForm(data={})

        assert not form.is_valid()
        assert form.errors == {
            "how_long": ["This field is required."],
            "investigated": ["This field is required."],
            "where_located": ["This field is required."],
        }

    def test_missing_conditionally_required_fields(self):
        form = LumpForm(
            data={
                "where_located": RightLeftOtherChoices.OTHER,
                "how_long": WhenStartedChoices.SINCE_A_SPECIFIC_DATE,
                "investigated": YesNo.YES,
            }
        )
        assert not form.is_valid()
        assert form.errors == {
            "other_area_description": ["This field is required."],
            "specific_date": ["This field is required."],
            "investigated_details": ["This field is required."],
        }

    def test_valid_form_with_conditionally_required_fields(self):
        form = LumpForm(
            data={
                "where_located": RightLeftOtherChoices.OTHER,
                "how_long": WhenStartedChoices.SINCE_A_SPECIFIC_DATE,
                "investigated": YesNo.YES,
                "other_area_description": "abc",
                "specific_date_0": "2",
                "specific_date_1": "2025",
                "investigated_details": "def",
            }
        )
        assert form.is_valid()

    @pytest.mark.django_db
    def test_save(self, clinical_user):
        appointment = AppointmentFactory.create()
        request = RequestFactory().get(
            reverse("mammograms:add_symptom_lump", kwargs={"pk": appointment.pk})
        )
        request.user = clinical_user

        form = LumpForm(
            data={
                "where_located": RightLeftOtherChoices.OTHER,
                "how_long": WhenStartedChoices.SINCE_A_SPECIFIC_DATE,
                "investigated": YesNo.YES,
                "other_area_description": "abc",
                "specific_date_0": "2",
                "specific_date_1": "2025",
                "investigated_details": "def",
            }
        )

        assert form.is_valid()

        obj = form.save(appointment=appointment, request=request)

        assert obj.appointment == appointment
        assert obj.symptom_type_id == SymptomType.LUMP
        assert obj.area == SymptomAreas.OTHER
        assert obj.area_description == "abc"
        assert obj.investigated

        # FIXME: need to add a new field to the model
        # assert obj.investigated_details == "def"

        assert obj.when_started == WhenStartedChoices.SINCE_A_SPECIFIC_DATE
        assert obj.year_started == 2025
        assert obj.month_started == 2
