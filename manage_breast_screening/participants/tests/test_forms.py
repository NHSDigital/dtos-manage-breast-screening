from datetime import date
from urllib.parse import urlencode

import pytest
from dateutil.relativedelta import relativedelta
from django.http import QueryDict
from pytest_django.asserts import assertFormError

from manage_breast_screening.clinics.tests.factories import ProviderFactory

from ..forms import EthnicityForm, ParticipantReportedMammogramForm
from ..models import ParticipantReportedMammogram
from .factories import AppointmentFactory, ParticipantFactory


@pytest.mark.django_db
class TestEthnicityForm:
    def test_init_with_saved_ethnicity(self):
        participant = ParticipantFactory.build(
            ethnic_background_id="english_welsh_scottish_ni_british",
        )
        form = EthnicityForm(
            participant=participant,
        )
        assert (
            form.initial["ethnic_background_choice"]
            == "english_welsh_scottish_ni_british"
        )

    def test_init_with_saved_non_specific_ethnicity(self):
        participant = ParticipantFactory.build(
            ethnic_background_id="any_other_white_background",
            any_other_background_details="an ethnicity",
        )
        form = EthnicityForm(
            participant=participant,
        )
        assert form.initial["ethnic_background_choice"] == "any_other_white_background"
        assert form.initial["any_other_white_background_details"] == "an ethnicity"

    def test_save_with_missing_data(self):
        form_data = {
            "ethnic_background_choice": "",
        }
        form = EthnicityForm(
            form_data,
            participant=ParticipantFactory.build(),
        )
        assertFormError(
            form, "ethnic_background_choice", ["Select an ethnic background"]
        )

    def test_save_a_specific_ethnicity(self):
        form_data = {
            "ethnic_background_choice": "english_welsh_scottish_ni_british",
        }
        form = EthnicityForm(
            form_data,
            participant=ParticipantFactory.build(),
        )
        form.is_valid()
        form.save()

        assert (
            form.participant.ethnic_background_id == "english_welsh_scottish_ni_british"
        )

    def test_save_a_non_specific_ethnicity(self):
        form_data = {
            "ethnic_background_choice": "any_other_white_background",
            "any_other_white_background_details": "",
        }
        form = EthnicityForm(
            form_data,
            participant=ParticipantFactory.build(),
        )
        form.is_valid()
        form.save()

        assert form.participant.ethnic_background_id == "any_other_white_background"
        assert form.participant.any_other_background_details == ""

    def test_save_a_non_specific_ethnicity_with_details(self):
        form_data = {
            "ethnic_background_choice": "any_other_white_background",
            "any_other_white_background_details": "an ethnicity",
        }
        form = EthnicityForm(
            form_data,
            participant=ParticipantFactory.build(),
        )
        form.is_valid()
        form.save()

        assert form.participant.ethnic_background_id == "any_other_white_background"
        assert form.participant.any_other_background_details == "an ethnicity"

    def test_save_when_existing_non_specific_ethnicity(self):
        participant = ParticipantFactory.create(
            ethnic_background_id="any_other_white_background",
            any_other_background_details="an ethnicity",
        )
        form_data = {
            "ethnic_background_choice": "any_other_asian_background",
            "any_other_white_background_details": "an ethnicity",
            "any_other_asian_background_details": "another ethnicity",
        }
        form = EthnicityForm(
            form_data,
            participant=participant,
        )
        form.is_valid()
        form.save()

        participant.refresh_from_db()
        assert participant.ethnic_background_id == "any_other_asian_background"
        assert participant.any_other_background_details == "another ethnicity"


@pytest.mark.django_db
class TestParticipantReportedMammogramForm:
    @pytest.fixture
    def appointment(self):
        participant = ParticipantFactory.create(first_name="Jane", last_name="Oldname")
        return AppointmentFactory(screening_episode__participant=participant)

    @pytest.fixture
    def most_recent_provider(self):
        return ProviderFactory.create()

    def test_no_choices_selected(self, appointment, most_recent_provider):
        form = ParticipantReportedMammogramForm(
            QueryDict(),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert not form.is_valid()
        assert form.errors == {
            "location_type": ["Select where the breast x-rays were taken"],
            "when_taken": ["Select when the x-rays were taken"],
            "name_is_the_same": ["Select if the x-rays were taken with the same name"],
        }

    def test_no_details_provided(self, appointment, most_recent_provider):
        form = ParticipantReportedMammogramForm(
            QueryDict(
                urlencode(
                    {
                        "location_type": ParticipantReportedMammogram.LocationType.ELSEWHERE_UK.value,
                        "when_taken": "APPROX",
                        "name_is_the_same": "NO",
                    },
                    doseq=True,
                )
            ),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert not form.is_valid()
        assert form.errors == {
            "approx_date": ["Enter the approximate date when the x-rays were taken"],
            "different_name": ["Enter the name the x-rays were taken with"],
            "somewhere_in_the_uk_details": [
                "Enter the clinic or hospital name, or any location details"
            ],
        }

    def test_invalid_date(self, appointment, most_recent_provider, time_machine):
        time_machine.move_to(date(2025, 5, 1))
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.ELSEWHERE_UK,
            "somewhere_in_the_uk_details": "XYZ provider",
            "when_taken": "EXACT",
            "name_is_the_same": "YES",
            "exact_date_0": "2",
            "exact_date_1": "5",
            "exact_date_2": "2025",
        }
        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )

        assert not form.is_valid()
        assert form.errors == {
            "exact_date": [
                "Enter a date before 1 May 2025",
                "Enter the date when the x-rays were taken",
            ]
        }

    def test_mammogram_in_same_provider(self, appointment, most_recent_provider):
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT.value,
            "when_taken": "NOT_SURE",
            "name_is_the_same": "YES",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert form.is_valid(), form.errors

        instance = form.create(appointment)

        assert instance.appointment == appointment
        assert instance.provider == most_recent_provider
        assert instance.location_type == "NHS_BREAST_SCREENING_UNIT"
        assert instance.location_details == ""
        assert instance.exact_date is None
        assert instance.approx_date == ""
        assert instance.different_name == ""
        assert instance.additional_information == ""

    def test_mammogram_in_uk(self, appointment, most_recent_provider):
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.ELSEWHERE_UK,
            "somewhere_in_the_uk_details": "XYZ provider",
            "when_taken": "NOT_SURE",
            "name_is_the_same": "YES",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert form.is_valid(), form.errors

        instance = form.create(appointment)

        assert instance.appointment == appointment
        assert instance.provider is None
        assert instance.location_type == "ELSEWHERE_UK"
        assert instance.location_details == "XYZ provider"
        assert instance.exact_date is None
        assert instance.approx_date == ""
        assert instance.different_name == ""
        assert instance.additional_information == ""

    def test_mammogram_outside_uk(self, appointment, most_recent_provider):
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.OUTSIDE_UK,
            "outside_the_uk_details": "XYZ provider",
            "when_taken": "NOT_SURE",
            "name_is_the_same": "YES",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert form.is_valid(), form.errors

        instance = form.create(appointment)

        assert instance.appointment == appointment
        assert instance.provider is None
        assert instance.location_type == "OUTSIDE_UK"
        assert instance.location_details == "XYZ provider"
        assert instance.exact_date is None
        assert instance.approx_date == ""
        assert instance.different_name == ""
        assert instance.additional_information == ""

    def test_mammogram_prefer_not_to_say(self, appointment, most_recent_provider):
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.PREFER_NOT_TO_SAY,
            "when_taken": "NOT_SURE",
            "name_is_the_same": "YES",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert form.is_valid(), form.errors

        instance = form.create(appointment)

        assert instance.appointment == appointment
        assert instance.provider is None
        assert instance.location_type == "PREFER_NOT_TO_SAY"
        assert instance.location_details == ""
        assert instance.exact_date is None
        assert instance.approx_date == ""
        assert instance.different_name == ""
        assert instance.additional_information == ""

    @pytest.mark.parametrize(
        "exact_date",
        [
            date.today(),
            date.today() - relativedelta(months=6) + relativedelta(days=2),
            date.today() - relativedelta(months=6) + relativedelta(days=1),
            date.today() - relativedelta(months=6),
            date.today() - relativedelta(months=6) - relativedelta(days=1),
            date.today() - relativedelta(years=50),
        ],
    )
    def test_mammogram_exact_date(self, appointment, most_recent_provider, exact_date):
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.PREFER_NOT_TO_SAY,
            "when_taken": "EXACT",
            "exact_date_0": exact_date.day,
            "exact_date_1": exact_date.month,
            "exact_date_2": exact_date.year,
            "name_is_the_same": "YES",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert form.is_valid(), form.errors

        instance = form.create(appointment)

        assert instance.appointment == appointment
        assert instance.provider is None
        assert instance.location_type == "PREFER_NOT_TO_SAY"
        assert instance.location_details == ""
        assert instance.exact_date == exact_date
        assert instance.approx_date == ""
        assert instance.different_name == ""
        assert instance.additional_information == ""

    def test_mammogram_approx_date(self, appointment, most_recent_provider):
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.PREFER_NOT_TO_SAY,
            "when_taken": "APPROX",
            "approx_date": "5 years ago",
            "name_is_the_same": "YES",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert form.is_valid(), form.errors

        instance = form.create(appointment)

        assert instance.appointment == appointment
        assert instance.provider is None
        assert instance.location_type == "PREFER_NOT_TO_SAY"
        assert instance.location_details == ""
        assert instance.exact_date is None
        assert instance.approx_date == "5 years ago"
        assert instance.different_name == ""
        assert instance.additional_information == ""

    def test_mammogram_different_name(self, appointment, most_recent_provider):
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.PREFER_NOT_TO_SAY,
            "when_taken": "NOT_SURE",
            "name_is_the_same": "NO",
            "different_name": "Jane Newname",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert form.is_valid(), form.errors

        instance = form.create(appointment)

        assert instance.appointment == appointment
        assert instance.provider is None
        assert instance.location_type == "PREFER_NOT_TO_SAY"
        assert instance.location_details == ""
        assert instance.exact_date is None
        assert instance.approx_date == ""
        assert instance.different_name == "Jane Newname"
        assert instance.additional_information == ""

    def test_full_details(self, appointment, most_recent_provider):
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.OUTSIDE_UK,
            "outside_the_uk_details": "XYZ provider",
            "when_taken": "APPROX",
            "approx_date": "5 years ago",
            "name_is_the_same": "NO",
            "different_name": "Jane Newname",
            "additional_information": "abcdef",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
        )
        assert form.is_valid(), form.errors

        instance = form.create(appointment)

        assert instance.appointment == appointment
        assert instance.provider is None
        assert instance.location_type == "OUTSIDE_UK"
        assert instance.location_details == "XYZ provider"
        assert instance.exact_date is None
        assert instance.approx_date == "5 years ago"
        assert instance.different_name == "Jane Newname"
        assert instance.additional_information == "abcdef"

    def test_update_full_details(self, appointment, most_recent_provider):
        original_instance = ParticipantReportedMammogram.objects.create(
            appointment=appointment,
            location_type=ParticipantReportedMammogram.LocationType.PREFER_NOT_TO_SAY,
        )
        data = {
            "location_type": ParticipantReportedMammogram.LocationType.OUTSIDE_UK,
            "outside_the_uk_details": "XYZ provider",
            "when_taken": "APPROX",
            "approx_date": "5 years ago",
            "name_is_the_same": "NO",
            "different_name": "Jane Newname",
            "additional_information": "abcdef",
        }

        form = ParticipantReportedMammogramForm(
            QueryDict(urlencode(data, doseq=True)),
            participant=appointment.screening_episode.participant,
            most_recent_provider=most_recent_provider,
            instance=original_instance,
        )
        assert form.is_valid(), form.errors

        updated_instance = form.update()

        assert updated_instance.pk == original_instance.pk
        assert updated_instance.appointment == appointment
        assert updated_instance.provider is None
        assert updated_instance.location_type == "OUTSIDE_UK"
        assert updated_instance.location_details == "XYZ provider"
        assert updated_instance.exact_date is None
        assert updated_instance.approx_date == "5 years ago"
        assert updated_instance.different_name == "Jane Newname"
        assert updated_instance.additional_information == "abcdef"
