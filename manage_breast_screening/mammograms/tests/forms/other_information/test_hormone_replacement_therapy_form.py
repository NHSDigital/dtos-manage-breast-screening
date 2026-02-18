from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.models.other_information.hormone_replacement_therapy import (
    HormoneReplacementTherapy,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    HormoneReplacementTherapyFactory,
)

from ....forms.other_information.hormone_replacement_therapy_form import (
    HormoneReplacementTherapyForm,
)


@pytest.mark.django_db
class TestHormoneReplacementTherapyForm:
    @pytest.fixture
    def appointment(self):
        return AppointmentFactory()

    @pytest.fixture
    def instance(self, appointment):
        return HormoneReplacementTherapyFactory(
            appointment=appointment,
            status=HormoneReplacementTherapy.Status.YES,
            approx_start_date="June 2020",
        )

    def test_create_with_no_data(self, appointment):
        form = HormoneReplacementTherapyForm(
            QueryDict(), participant=appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {
            "status": ["Select whether they are currently taking HRT or not"]
        }

    def test_update_with_no_data(self, instance):
        form = HormoneReplacementTherapyForm(
            QueryDict(), instance=instance, participant=instance.appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {
            "status": ["Select whether they are currently taking HRT or not"]
        }

    def test_missing_details_when_yes(self, appointment):
        form = HormoneReplacementTherapyForm(
            QueryDict(
                urlencode({"status": HormoneReplacementTherapy.Status.YES}, doseq=True)
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "approx_start_date": [
                "Provide approximate date when they started taking HRT"
            ]
        }

    def test_missing_details_when_no_but_stopped_recently(self, appointment):
        form = HormoneReplacementTherapyForm(
            QueryDict(
                urlencode(
                    {
                        "status": HormoneReplacementTherapy.Status.NO_BUT_STOPPED_RECENTLY
                    },
                    doseq=True,
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "approx_end_date": [
                "Provide approximate date when they stopped taking HRT"
            ],
            "approx_previous_duration": [
                "Provide approximate time they were taking HRT for"
            ],
        }

    success_test_cases = [
        {
            "status": HormoneReplacementTherapy.Status.YES,
            "approx_start_date": "August 2024",
        },
        {
            "status": HormoneReplacementTherapy.Status.NO_BUT_STOPPED_RECENTLY,
            "approx_end_date": "Summer 2025",
            "approx_previous_duration": "5 years 6 months",
        },
        {
            "status": HormoneReplacementTherapy.Status.NO,
        },
    ]

    @pytest.mark.parametrize(
        "data",
        success_test_cases,
    )
    def test_create_success(self, appointment, data):
        form = HormoneReplacementTherapyForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment)
        assert obj.appointment == appointment
        assert obj.status == data.get("status")
        assert obj.approx_start_date == data.get("approx_start_date", "")
        assert obj.approx_end_date == data.get("approx_end_date", "")
        assert obj.approx_previous_duration == data.get("approx_previous_duration", "")

    @pytest.mark.parametrize(
        "data",
        success_test_cases,
    )
    def test_update_success(self, instance, data):
        appointment = instance.appointment
        form = HormoneReplacementTherapyForm(
            QueryDict(urlencode(data, doseq=True)),
            instance=instance,
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.update()
        assert obj.pk == instance.pk
        assert obj.appointment == appointment
        assert obj.status == data.get("status")
        assert obj.approx_start_date == data.get("approx_start_date", "")
        assert obj.approx_end_date == data.get("approx_end_date", "")
        assert obj.approx_previous_duration == data.get("approx_previous_duration", "")
