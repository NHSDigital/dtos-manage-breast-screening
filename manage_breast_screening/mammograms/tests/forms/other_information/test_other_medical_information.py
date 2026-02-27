from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    OtherMedicalInformationFactory,
)

from ....forms.other_information.other_medical_information_form import (
    OtherMedicalInformationForm,
)


@pytest.mark.django_db
class TestOtherMedicalInformationForm:
    @pytest.fixture
    def appointment(self):
        return AppointmentFactory()

    @pytest.fixture
    def instance(self, appointment):
        return OtherMedicalInformationFactory(appointment=appointment)

    def test_create_with_no_data(self, appointment):
        form = OtherMedicalInformationForm(
            QueryDict(), participant=appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {
            "details": [
                "Provide details of any relevant health conditions or medications that are not covered by symptoms or medical history questions"
            ]
        }

    def test_update_with_no_data(self, instance):
        form = OtherMedicalInformationForm(
            QueryDict(), instance=instance, participant=instance.appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {
            "details": [
                "Provide details of any relevant health conditions or medications that are not covered by symptoms or medical history questions"
            ]
        }

    def test_create_success(self, appointment):
        form = OtherMedicalInformationForm(
            QueryDict(
                urlencode({"details": "some other medical information"}, doseq=True)
            ),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment)
        assert obj.appointment == appointment
        assert obj.details == "some other medical information"

    def test_update_success(self, instance):
        appointment = instance.appointment
        form = OtherMedicalInformationForm(
            QueryDict(
                urlencode({"details": "updated medical information"}, doseq=True)
            ),
            instance=instance,
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.update()
        assert obj.pk == instance.pk
        assert obj.appointment == appointment
        assert obj.details == "updated medical information"
