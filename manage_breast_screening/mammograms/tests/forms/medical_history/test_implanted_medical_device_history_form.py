import datetime
from urllib.parse import urlencode

import pytest
from django.http import QueryDict
from django.test import RequestFactory

from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ImplantedMedicalDeviceHistoryItemFactory,
)

from ....forms.medical_history.implanted_medical_device_history_form import (
    ImplantedMedicalDeviceHistoryForm,
    ImplantedMedicalDeviceHistoryUpdateForm,
)


@pytest.fixture
def dummy_request(clinical_user):
    request = RequestFactory().get("/test-form")
    request.user = clinical_user
    return request


@pytest.mark.django_db
class TestImplantedMedicalDeviceHistoryForm:
    def test_no_data(self):
        appointment = AppointmentFactory()
        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(), participant=appointment.participant
        )

        assert not form.is_valid()
        assert form.errors == {"device": ["Select the device type"]}

    def test_other_device_without_information(self):
        appointment = AppointmentFactory()

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

    def test_procedure_year_invalid_format(self):
        appointment = AppointmentFactory()

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
        assert form.errors == {"procedure_year": ["Enter a whole number."]}

    def test_removal_year_invalid_format(self):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "device_has_been_removed": True,
                        "removal_year": "qwerty",
                    },
                )
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
    def test_removal_year_outside_range(self, removal_year):
        appointment = AppointmentFactory()

        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            (f"Year must be {max_year} or earlier")
            if removal_year > max_year
            else (f"Year must be {min_year} or later")
        )
        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "device_has_been_removed": True,
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

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "procedure_year": procedure_year,
                        "device_has_been_removed": True,
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

    def test_removal_year_when_not_removed(self, dummy_request):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                        "procedure_year": 2010,
                        "removal_year": 1900,
                        "additional_details": "removal_year provided but not device_has_been_removed",
                    },
                    doseq=True,
                )
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

        obj = form.create(appointment=appointment, request=dummy_request)

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
    def test_success(self, data, dummy_request):
        appointment = AppointmentFactory()

        form = ImplantedMedicalDeviceHistoryForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment, request=dummy_request)

        assert obj.appointment == appointment
        assert obj.device == data.get("device")
        assert obj.other_medical_device_details == data.get(
            "other_medical_device_details", ""
        )
        assert obj.procedure_year == data.get("procedure_year", None)
        assert obj.removal_year == data.get("removal_year", None)
        assert obj.additional_details == data.get("additional_details", "")


@pytest.mark.django_db
class TestImplantedMedicalDeviceHistoryUpdateForm:
    @pytest.fixture
    def instance(self):
        return ImplantedMedicalDeviceHistoryItemFactory(
            device=ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE
        )

    def test_no_data(self, instance):
        form = ImplantedMedicalDeviceHistoryUpdateForm(instance, QueryDict())

        assert not form.is_valid()
        assert form.errors == {"device": ["Select the device type"]}

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
    def test_success(self, instance, data, dummy_request):
        form = ImplantedMedicalDeviceHistoryUpdateForm(
            instance,
            QueryDict(urlencode(data, doseq=True)),
        )

        assert form.is_valid()

        obj = form.update(request=dummy_request)

        assert obj.appointment == instance.appointment
        assert obj.device == data.get("device")
        assert obj.other_medical_device_details == data.get(
            "other_medical_device_details", ""
        )
        assert obj.procedure_year == data.get("procedure_year", None)
        assert obj.removal_year == data.get("removal_year", None)
        assert obj.additional_details == data.get("additional_details", "")
