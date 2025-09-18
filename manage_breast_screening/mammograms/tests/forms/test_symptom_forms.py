import pytest
from django.test import RequestFactory

from manage_breast_screening.mammograms.forms.symptom_forms import (
    LumpForm,
    RelativeDateChoices,
    RightLeftOtherChoices,
)
from manage_breast_screening.nhsuk_forms.choices import YesNo
from manage_breast_screening.participants.models.symptom import (
    SymptomAreas,
    SymptomType,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


class TestLumpForm:
    def test_valid_form(self):
        form = LumpForm(
            data={
                "area": RightLeftOtherChoices.LEFT_BREAST,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS,
                "investigated": YesNo.NO,
            }
        )
        assert form.is_valid()

    def test_missing_required_fields(self):
        form = LumpForm(data={})

        assert not form.is_valid()
        assert form.errors == {
            "when_started": ["Select how long the symptom has existed"],
            "investigated": ["Select whether the lump has been investigated or not"],
            "area": ["Select the location of the lump"],
        }

    def test_missing_conditionally_required_fields(self):
        form = LumpForm(
            data={
                "area": RightLeftOtherChoices.OTHER,
                "when_started": RelativeDateChoices.SINCE_A_SPECIFIC_DATE,
                "investigated": YesNo.YES,
            }
        )

        assert not form.is_valid()
        assert form.errors == {
            "area_description": [
                "Describe the specific area where the lump is located"
            ],
            "specific_date": ["Enter the date the symptom started"],
            "investigation_details": ["Enter details of any investigations"],
        }

    def test_valid_form_with_conditionally_required_fields(self):
        form = LumpForm(
            data={
                "area": RightLeftOtherChoices.OTHER,
                "when_started": RelativeDateChoices.SINCE_A_SPECIFIC_DATE,
                "investigated": YesNo.YES,
                "area_description": "abc",
                "specific_date_0": "2",
                "specific_date_1": "2025",
                "investigation_details": "def",
            }
        )
        assert form.is_valid()

    @pytest.mark.django_db
    def test_save(self, clinical_user):
        appointment = AppointmentFactory.create()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = LumpForm(
            data={
                "area": RightLeftOtherChoices.OTHER,
                "when_started": RelativeDateChoices.SINCE_A_SPECIFIC_DATE,
                "investigated": YesNo.YES,
                "area_description": "abc",
                "specific_date_0": "2",
                "specific_date_1": "2025",
                "investigation_details": "def",
            }
        )

        assert form.is_valid()

        obj = form.save(appointment=appointment, request=request)

        assert obj.appointment == appointment
        assert obj.symptom_type_id == SymptomType.LUMP
        assert obj.area == SymptomAreas.OTHER
        assert obj.area_description == "abc"
        assert obj.investigated
        assert obj.investigation_details == "def"
        assert obj.when_started == RelativeDateChoices.SINCE_A_SPECIFIC_DATE
        assert obj.year_started == 2025
        assert obj.month_started == 2

    @pytest.mark.django_db
    def test_hidden_conditional_fields_not_persisted(self, clinical_user):
        appointment = AppointmentFactory.create()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = LumpForm(
            data={
                "area": RightLeftOtherChoices.RIGHT_BREAST,
                "when_started": RelativeDateChoices.NOT_SURE,
                "investigated": YesNo.NO,
                "area_description": "abc",
                "specific_date_0": "2",
                "specific_date_1": "2025",
                "investigation_details": "def",
            }
        )

        assert form.is_valid()

        obj = form.save(appointment=appointment, request=request)

        assert not obj.area_description
        assert not obj.investigation_details
        assert not obj.year_started
        assert not obj.month_started
