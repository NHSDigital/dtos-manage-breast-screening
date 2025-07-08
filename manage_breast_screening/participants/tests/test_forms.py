import pytest
from pytest_django.asserts import assertFormError

from manage_breast_screening.clinics.tests.factories import ProviderFactory

from ..forms import EthnicityForm, ParticipantRecordedMammogramForm
from .factories import ParticipantFactory


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
class TestParticipantRecordedMammogramForm:
    @pytest.fixture
    def participant(self):
        return ParticipantFactory.create(first_name="Jane", last_name="Oldname")

    @pytest.fixture
    def current_provider(self):
        return ProviderFactory.create()

    def test_no_choices_selected(self, participant, current_provider):
        form = ParticipantRecordedMammogramForm(participant, current_provider, {})
        assert not form.is_valid()
        assert form.errors == {
            "where_taken": ["This field is required."],
            "when_taken": ["This field is required."],
            "name_is_the_same": ["This field is required."],
        }

    def test_no_details_provided(self, participant, current_provider):
        form = ParticipantRecordedMammogramForm(
            participant,
            current_provider,
            {
                "where_taken": ParticipantRecordedMammogramForm.WhereTaken.ELSEWHERE_UK.value,
                "when_taken": "approx",
                "name_is_the_same": "no",
            },
        )
        assert not form.is_valid()
        assert form.errors == {
            "approx_date": ["Enter the approximate date when the x-rays were taken"],
            "different_name": ["Enter the name the x-rays were taken with"],
            "location_details": [
                "Enter the clinic or hospital name, or any location details"
            ],
        }

    def test_no_provider_selected(self, participant, current_provider):
        form = ParticipantRecordedMammogramForm(
            participant,
            current_provider,
            {
                "where_taken": ParticipantRecordedMammogramForm.WhereTaken.ANOTHER_UNIT.value,
                "when_taken": "approx",
                "approx_date": "5 years ago",
                "name_is_the_same": "yes",
            },
        )
        assert not form.is_valid()
        assert form.errors == {
            "provider": ["Select another brest screening unit."],
        }

    def test_mammogram_in_same_provider(self, participant, current_provider):
        data = {
            "where_taken": ParticipantRecordedMammogramForm.WhereTaken.SAME_UNIT.value,
            "when_taken": "approx",
            "name_is_the_same": "yes",
            "approx_date": "5 years ago",
        }

        form = ParticipantRecordedMammogramForm(participant, current_provider, data)
        assert form.is_valid(), form.errors

        instance = form.save(commit=False)

        assert instance.participant == participant
        assert instance.provider == current_provider
        assert instance.location_type == "NHS_BREAST_SCREENING_UNIT"
        assert instance.location_details == ""

    def test_mammogram_in_different_provider(self, participant, current_provider):
        other_provider = ProviderFactory.create()
        data = {
            "where_taken": ParticipantRecordedMammogramForm.WhereTaken.ANOTHER_UNIT,
            "provider": other_provider.pk,
            "when_taken": "approx",
            "name_is_the_same": "yes",
            "approx_date": "5 years ago",
        }

        form = ParticipantRecordedMammogramForm(participant, current_provider, data)
        assert form.is_valid(), form.errors

        instance = form.save(commit=False)

        assert instance.participant == participant
        assert instance.provider == other_provider
        assert instance.location_type == "NHS_BREAST_SCREENING_UNIT"
        assert instance.location_details == ""

    def test_mammogram_elsewhere_in_uk(self, participant, current_provider):
        data = {
            "where_taken": ParticipantRecordedMammogramForm.WhereTaken.ELSEWHERE_UK,
            "location_details": "XYZ provider",
            "when_taken": "approx",
            "name_is_the_same": "yes",
            "approx_date": "5 years ago",
        }

        form = ParticipantRecordedMammogramForm(participant, current_provider, data)
        assert form.is_valid(), form.errors

        instance = form.save(commit=False)

        assert instance.participant == participant
        assert instance.provider is None
        assert instance.location_type == "ELSEWHERE_UK"
        assert instance.location_details == "XYZ provider"

    def test_mammogram_prefer_not_to_say(self, participant, current_provider):
        data = {
            "where_taken": ParticipantRecordedMammogramForm.WhereTaken.PREFER_NOT_TO_SAY,
            "when_taken": "approx",
            "name_is_the_same": "yes",
            "approx_date": "5 years ago",
        }

        form = ParticipantRecordedMammogramForm(participant, current_provider, data)
        assert form.is_valid(), form.errors

        instance = form.save(commit=False)

        assert instance.participant == participant
        assert instance.provider is None
        assert instance.location_type == "PREFER_NOT_TO_SAY"

    def test_full_details(self, participant, current_provider):
        data = {
            "where_taken": ParticipantRecordedMammogramForm.WhereTaken.ELSEWHERE_UK,
            "location_details": "XYZ provider",
            "when_taken": "approx",
            "approx_date": "5 years ago",
            "name_is_the_same": "no",
            "different_name": "Jane Newname",
            "additional_information": "abcdef",
        }

        form = ParticipantRecordedMammogramForm(participant, current_provider, data)
        assert form.is_valid(), form.errors

        instance = form.save(commit=False)

        assert instance.participant == participant
        assert instance.provider is None
        assert instance.location_type == "ELSEWHERE_UK"
        assert instance.location_details == "XYZ provider"
        assert instance.exact_date is None
        assert instance.approx_date == "5 years ago"
        assert instance.different_name == "Jane Newname"
        assert instance.additional_information == "abcdef"
