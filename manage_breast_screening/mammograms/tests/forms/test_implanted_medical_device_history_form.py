import datetime
from urllib.parse import urlencode

import pytest
from django.http import QueryDict
from django.test import RequestFactory

from manage_breast_screening.participants.models.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ...forms.implanted_medical_device_history_form import (
    ImplantedMedicalDeviceHistoryForm,
    RemovalStatusChoices,
)


@pytest.mark.django_db
class TestImplantedMedicalDeviceHistoryForm:
    def test_no_data(self, clinical_user):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(), participant=appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {"device": ["Select the device type"]}

    def test_other_device_without_information(self, clinical_user):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "other_medical_device_details": ["Provide details of the device"]
        }

    def test_procedure_year_invalid_format(self, clinical_user):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "procedure_year": "qwerty",
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {"procedure_year": ["Enter year as a number."]}

    def test_removal_year_invalid_format(self, clinical_user):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "removal_status": RemovalStatusChoices.HAS_BEEN_REMOVED,
                        "removal_year": "qwerty",
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": [
                "Enter year as a number.",
                "Enter the year the device was removed",
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
    def test_procedure_year_outside_range(self, clinical_user, procedure_year):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            f"Year should be between {min_year} and {max_year}."
        )
        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "procedure_year": procedure_year,
                    },
                )
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
    def test_removal_year_outside_range(self, clinical_user, removal_year):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            f"Year should be between {min_year} and {max_year}."
        )
        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "removal_status": RemovalStatusChoices.HAS_BEEN_REMOVED,
                        "removal_year": removal_year,
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": [
                year_outside_range_error_message,
                "Enter the year the device was removed",
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
    def test_removal_year_before_procedure_year(
        self, clinical_user, procedure_year, removal_year
    ):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "procedure_year": procedure_year,
                        "removal_status": RemovalStatusChoices.HAS_BEEN_REMOVED,
                        "removal_year": removal_year,
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": ["Year removed cannot be before year of procedure"]
        }

    def test_has_been_removed_without_removal_date(self, clinical_user):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "removal_status": RemovalStatusChoices.HAS_BEEN_REMOVED,
                    },
                )
            ),
            participant=appointment.participant,
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": ["Enter the year the device was removed"]
        }

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
                "removal_status": RemovalStatusChoices.HAS_BEEN_REMOVED,
                "removal_year": 2015,
                "additional_details": "Some additional details",
            },
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                "procedure_year": 2015,
                "removal_status": RemovalStatusChoices.HAS_BEEN_REMOVED,
                "removal_year": 2015,
            },
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                "procedure_year": 2010,
            },
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                "removal_status": RemovalStatusChoices.HAS_BEEN_REMOVED,
                "removal_year": 2015,
            },
        ],
    )
    def test_success(self, clinical_user, data):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment, request=request)

        assert obj.appointment == appointment
        assert obj.device == data.get("device")
        assert obj.other_medical_device_details == data.get(
            "other_medical_device_details", ""
        )
        assert obj.procedure_year == data.get("procedure_year", None)
        assert obj.removal_year == data.get("removal_year", None)
        assert obj.additional_details == data.get("additional_details", "")
