from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.models.other_information.pregnancy_and_breastfeeding import (
    PregnancyAndBreastfeeding,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    PregnancyAndBreastfeedingFactory,
)

from ....forms.other_information.pregnancy_and_breastfeeding_form import (
    PregnancyAndBreastfeedingForm,
)


@pytest.mark.django_db
class TestPregnancyAndBreastfeedingForm:
    @pytest.fixture
    def appointment(self):
        return AppointmentFactory()

    @pytest.fixture
    def instance(self, appointment):
        return PregnancyAndBreastfeedingFactory(
            appointment=appointment,
            pregnancy_status=PregnancyAndBreastfeeding.PregnancyStatus.NO,
            breastfeeding_status=PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
        )

    def test_create_with_no_data(self, appointment):
        form = PregnancyAndBreastfeedingForm(
            QueryDict(), participant=appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {
            "pregnancy_status": ["Select whether they are currently pregnant or not"],
            "breastfeeding_status": [
                "Select whether they are currently breastfeeding or not"
            ],
        }

    def test_update_with_no_data(self, instance):
        form = PregnancyAndBreastfeedingForm(
            QueryDict(), instance=instance, participant=instance.appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {
            "pregnancy_status": ["Select whether they are currently pregnant or not"],
            "breastfeeding_status": [
                "Select whether they are currently breastfeeding or not"
            ],
        }

    def test_missing_approx_pregnancy_due_date(self, appointment):
        form = PregnancyAndBreastfeedingForm(
            QueryDict(
                urlencode(
                    {
                        "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.YES,
                        "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
                    },
                    doseq=True,
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "approx_pregnancy_due_date": ["Provide approximate due date"],
        }

    def test_missing_approx_pregnancy_end_date(self, appointment):
        form = PregnancyAndBreastfeedingForm(
            QueryDict(
                urlencode(
                    {
                        "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO_BUT_HAS_BEEN_RECENTLY,
                        "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
                    },
                    doseq=True,
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "approx_pregnancy_end_date": ["Provide approximate date pregnancy ended"],
        }

    def test_missing_approx_breastfeeding_start_date(self, appointment):
        form = PregnancyAndBreastfeedingForm(
            QueryDict(
                urlencode(
                    {
                        "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO,
                        "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.YES,
                    },
                    doseq=True,
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "approx_breastfeeding_start_date": [
                "Provide details of when they started breastfeeding"
            ],
        }

    def test_missing_approx_breastfeeding_end_date(self, appointment):
        form = PregnancyAndBreastfeedingForm(
            QueryDict(
                urlencode(
                    {
                        "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO,
                        "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO_BUT_STOPPED_RECENTLY,
                    },
                    doseq=True,
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "approx_breastfeeding_end_date": [
                "Provide details of when they stopped breastfeeding"
            ],
        }

    success_test_cases = [
        {
            "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO,
            "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
        },
        {
            "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO,
            "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.YES,
            "approx_breastfeeding_start_date": "Since January",
        },
        {
            "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO,
            "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO_BUT_STOPPED_RECENTLY,
            "approx_breastfeeding_end_date": "Two months ago",
        },
        {
            "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.YES,
            "approx_pregnancy_due_date": "Due in November",
            "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
        },
        {
            "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.NO_BUT_HAS_BEEN_RECENTLY,
            "approx_pregnancy_end_date": "Gave birth two weeks ago",
            "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
        },
        {
            "pregnancy_status": PregnancyAndBreastfeeding.PregnancyStatus.YES,
            "approx_pregnancy_due_date": "Due in November",
            "breastfeeding_status": PregnancyAndBreastfeeding.BreastfeedingStatus.YES,
            "approx_breastfeeding_start_date": "Since January",
        },
    ]

    @pytest.mark.parametrize(
        "data",
        success_test_cases,
    )
    def test_create_success(self, appointment, data):
        form = PregnancyAndBreastfeedingForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment)
        assert obj.appointment == appointment
        assert obj.pregnancy_status == data.get("pregnancy_status")
        assert obj.approx_pregnancy_due_date == data.get(
            "approx_pregnancy_due_date", ""
        )
        assert obj.approx_pregnancy_end_date == data.get(
            "approx_pregnancy_end_date", ""
        )
        assert obj.breastfeeding_status == data.get("breastfeeding_status")
        assert obj.approx_breastfeeding_start_date == data.get(
            "approx_breastfeeding_start_date", ""
        )
        assert obj.approx_breastfeeding_end_date == data.get(
            "approx_breastfeeding_end_date", ""
        )

    @pytest.mark.parametrize(
        "data",
        success_test_cases,
    )
    def test_update_success(self, instance, data):
        appointment = instance.appointment
        form = PregnancyAndBreastfeedingForm(
            QueryDict(urlencode(data, doseq=True)),
            instance=instance,
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.update()
        assert obj.pk == instance.pk
        assert obj.appointment == appointment
        assert obj.pregnancy_status == data.get("pregnancy_status")
        assert obj.approx_pregnancy_due_date == data.get(
            "approx_pregnancy_due_date", ""
        )
        assert obj.approx_pregnancy_end_date == data.get(
            "approx_pregnancy_end_date", ""
        )
        assert obj.breastfeeding_status == data.get("breastfeeding_status")
        assert obj.approx_breastfeeding_start_date == data.get(
            "approx_breastfeeding_start_date", ""
        )
        assert obj.approx_breastfeeding_end_date == data.get(
            "approx_breastfeeding_end_date", ""
        )
