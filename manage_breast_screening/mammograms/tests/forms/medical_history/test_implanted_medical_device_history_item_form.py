import datetime

import pytest
from django.http import QueryDict

from manage_breast_screening.conftest import make_query_dict
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ImplantedMedicalDeviceHistoryItemFactory,
)

from ....forms.medical_history.implanted_medical_device_history_item_form import (
    ImplantedMedicalDeviceHistoryItemForm,
)


@pytest.mark.django_db
class TestImplantedMedicalDeviceHistoryItemForm:
    def test_no_data(self):
        appointment = AppointmentFactory()
        form = ImplantedMedicalDeviceHistoryItemForm(
            QueryDict(), participant=appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {"device": ["Select the device type"]}

    def test_other_device_without_information(self):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryItemForm(
            make_query_dict(
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                }
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "other_medical_device_details": ["Provide details of the device"]
        }

    def test_procedure_year_invalid_format(self):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryItemForm(
            make_query_dict(
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "procedure_year": "qwerty",
                }
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {"procedure_year": ["Enter a whole number."]}

    def test_removal_year_invalid_format(self):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryItemForm(
            make_query_dict(
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "device_has_been_removed": True,
                    "removal_year": "qwerty",
                }
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": [
                "Enter a whole number.",
            ]
        }

    @pytest.mark.parametrize(
        "procedure_year",
        [
            -1,
            1900,
            datetime.date.today().year - 81,
            datetime.date.today().year + 1,
            3000,
        ],
    )
    def test_procedure_year_outside_range(self, procedure_year):
        appointment = AppointmentFactory()

        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            (f"Year must be {max_year} or earlier")
            if procedure_year > max_year
            else (f"Year must be {min_year} or later")
        )
        form = ImplantedMedicalDeviceHistoryItemForm(
            make_query_dict(
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "procedure_year": procedure_year,
                }
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {"procedure_year": [year_outside_range_error_message]}

    @pytest.mark.parametrize(
        "removal_year",
        [
            -1,
            1900,
            datetime.date.today().year - 81,
            datetime.date.today().year + 1,
            3000,
        ],
    )
    def test_removal_year_outside_range(self, removal_year):
        appointment = AppointmentFactory()

        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            (f"Year must be {max_year} or earlier")
            if removal_year > max_year
            else (f"Year must be {min_year} or later")
        )
        form = ImplantedMedicalDeviceHistoryItemForm(
            make_query_dict(
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "device_has_been_removed": True,
                    "removal_year": removal_year,
                }
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": [
                year_outside_range_error_message,
            ]
        }

    @pytest.mark.parametrize(
        "procedure_year,removal_year",
        [
            (datetime.date.today().year, datetime.date.today().year - 1),
            (datetime.date.today().year - 25, datetime.date.today().year - 30),
            (datetime.date.today().year - 79, datetime.date.today().year - 80),
        ],
    )
    def test_removal_year_before_procedure_year(self, procedure_year, removal_year):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryItemForm(
            make_query_dict(
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "procedure_year": procedure_year,
                    "device_has_been_removed": True,
                    "removal_year": removal_year,
                }
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": ["Year removed cannot be before year of procedure"]
        }

    def test_removal_year_when_not_removed(self):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryItemForm(
            make_query_dict(
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "procedure_year": 2010,
                    "removal_year": 1900,
                    "additional_details": "removal_year provided but not device_has_been_removed",
                }
            ),
            participant=appointment.participant,
        )

        # confirm full_clean removes removal_year but keeps procedure_year
        assert form.data["removal_year"] == "1900"
        form.full_clean()
        assert form.data["removal_year"] is None
        assert form.cleaned_data["removal_year"] is None
        assert form.cleaned_data["procedure_year"] == 2010

        assert form.is_valid()

        obj = form.create(appointment=appointment)

        obj.refresh_from_db()
        assert obj.appointment == appointment
        assert obj.device == ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE
        assert obj.procedure_year == 2010
        assert not obj.device_has_been_removed
        assert obj.removal_year is None
        assert (
            obj.additional_details
            == "removal_year provided but not device_has_been_removed"
        )

    @pytest.mark.parametrize(
        "data",
        [
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
            },
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                "other_medical_device_details": "Some details about the device",
                "procedure_year": 2010,
                "device_has_been_removed": True,
                "removal_year": 2015,
                "additional_details": "Some additional details",
            },
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                "procedure_year": 2015,
                "device_has_been_removed": True,
                "removal_year": 2015,
            },
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                "procedure_year": 2010,
            },
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                "device_has_been_removed": True,
                "removal_year": 2015,
            },
        ],
    )
    def test_valid_create(self, data):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryItemForm(
            make_query_dict(data),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment)

        assert obj.appointment == appointment
        assert obj.device == data.get("device")
        assert obj.other_medical_device_details == data.get(
            "other_medical_device_details", ""
        )
        assert obj.procedure_year == data.get("procedure_year", None)
        assert obj.removal_year == data.get("removal_year", None)
        assert obj.additional_details == data.get("additional_details", "")

    @pytest.fixture
    def instance(self):
        return ImplantedMedicalDeviceHistoryItemFactory(
            device=ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE
        )

    @pytest.mark.parametrize(
        "data",
        [
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
            },
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                "other_medical_device_details": "Some details about the device",
                "procedure_year": 2010,
                "device_has_been_removed": True,
                "removal_year": 2015,
                "additional_details": "Some additional details",
            },
        ],
    )
    def test_valid_update(self, instance, data):
        form = ImplantedMedicalDeviceHistoryItemForm(
            instance=instance,
            participant=instance.appointment.participant,
            data=make_query_dict(data),
        )

        assert form.is_valid()

        obj = form.update()

        assert obj.appointment == instance.appointment
        assert obj.device == data.get("device")
        assert obj.other_medical_device_details == data.get(
            "other_medical_device_details", ""
        )
        assert obj.procedure_year == data.get("procedure_year", None)
        assert obj.removal_year == data.get("removal_year", None)
        assert obj.additional_details == data.get("additional_details", "")
