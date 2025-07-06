import pytest
from pytest_django.asserts import assertFormError

from ..forms import EthnicityForm
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
