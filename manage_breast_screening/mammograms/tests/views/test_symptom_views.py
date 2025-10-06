import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.nhsuk_forms.choices import YesNo
from manage_breast_screening.participants.models.symptom import (
    NippleChangeChoices,
    RelativeDateChoices,
    SkinChangeChoices,
    Symptom,
    SymptomAreas,
)
from manage_breast_screening.participants.tests.factories import SymptomFactory


@pytest.fixture
def lump(appointment):
    return SymptomFactory.create(appointment=appointment, lump=True)


@pytest.mark.django_db
class TestAddLumpView:
    def test_renders_response(self, clinical_user_client, appointment):
        response = clinical_user_client.get(
            reverse(
                "mammograms:add_symptom_lump",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:add_symptom_lump",
                kwargs={"pk": appointment.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_invvalid_post_renders_response_with_errors(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:add_symptom_lump",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <div class="nhsuk-error-summary" aria-labelledby="error-summary-title" role="alert" tabindex="-1" data-module="nhsuk-error-summary">
                    <h2 class="nhsuk-error-summary__title" id="error-summary-title">There is a problem</h2>
                      <div class="nhsuk-error-summary__body">
                        <ul class="nhsuk-list nhsuk-error-summary__list" role="list">
                            <li><a href="#id_area">Select the location of the lump</a></li>
                            <li><a href="#id_when_started">Select how long the symptom has existed</a></li>
                            <li><a href="#id_investigated">Select whether the symptom has been investigated or not</a></li>
                        </ul>
                    </div>
                </div>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangeLumpView:
    @pytest.fixture
    def lump(self, appointment):
        return SymptomFactory.create(lump=True, appointment=appointment)

    def test_renders_response(self, clinical_user_client, appointment, lump):
        response = clinical_user_client.get(
            reverse(
                "mammograms:change_symptom_lump",
                kwargs={"pk": appointment.pk, "symptom_pk": lump.pk},
            )
        )
        assert response.status_code == 200

    def test_non_existant_or_deleted_symptom_id_is_a_404(
        self, clinical_user_client, appointment
    ):
        """
        Note: the behaviour we probably want here is to redirect back to
        the "parent page" when a child entity is not found, and use flash
        messages to explain the error. However, none of this is
        implemented yet.
        """
        response = clinical_user_client.get(
            reverse(
                "mammograms:change_symptom_lump",
                kwargs={
                    "pk": appointment.pk,
                    "symptom_pk": "beefbeef-beef-beef-beef-beefbeefbeef",
                },
            )
        )

        assert response.status_code == 404

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, lump
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:change_symptom_lump",
                kwargs={"pk": appointment.pk, "symptom_pk": lump.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_invvalid_post_renders_response_with_errors(
        self, clinical_user_client, appointment, lump
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:change_symptom_lump",
                kwargs={"pk": appointment.pk, "symptom_pk": lump.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <div class="nhsuk-error-summary" aria-labelledby="error-summary-title" role="alert" tabindex="-1" data-module="nhsuk-error-summary">
                    <h2 class="nhsuk-error-summary__title" id="error-summary-title">There is a problem</h2>
                      <div class="nhsuk-error-summary__body">
                        <ul class="nhsuk-list nhsuk-error-summary__list" role="list">
                            <li><a href="#id_area">Select the location of the lump</a></li>
                            <li><a href="#id_when_started">Select how long the symptom has existed</a></li>
                            <li><a href="#id_investigated">Select whether the symptom has been investigated or not</a></li>
                        </ul>
                    </div>
                </div>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestAddSkinChangeView:
    def test_renders_response(self, clinical_user_client, appointment):
        response = clinical_user_client.get(
            reverse(
                "mammograms:add_symptom_skin_change",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:add_symptom_skin_change",
                kwargs={"pk": appointment.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "symptom_sub_type": SkinChangeChoices.DIMPLES_OR_INDENTATION,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestChangeSkinChangeView:
    @pytest.fixture
    def colour_change(self, appointment):
        return SymptomFactory.create(colour_change=True, appointment=appointment)

    def test_renders_response(self, clinical_user_client, appointment, colour_change):
        response = clinical_user_client.get(
            reverse(
                "mammograms:change_symptom_skin_change",
                kwargs={"pk": appointment.pk, "symptom_pk": colour_change.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, colour_change
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:change_symptom_skin_change",
                kwargs={"pk": appointment.pk, "symptom_pk": colour_change.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "symptom_sub_type": SkinChangeChoices.COLOUR_CHANGE,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestAddNippleChangeView:
    def test_renders_response(self, clinical_user_client, appointment):
        response = clinical_user_client.get(
            reverse(
                "mammograms:add_symptom_nipple_change",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:add_symptom_nipple_change",
                kwargs={"pk": appointment.pk},
            ),
            {
                "area": [SymptomAreas.RIGHT_BREAST.value],
                "symptom_sub_type": NippleChangeChoices.BLOODY_DISCHARGE,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestChangeNippleChangeView:
    @pytest.fixture
    def inversion(self, appointment):
        return SymptomFactory.create(inversion=True, appointment=appointment)

    def test_renders_response(self, clinical_user_client, appointment, inversion):
        response = clinical_user_client.get(
            reverse(
                "mammograms:change_symptom_nipple_change",
                kwargs={"pk": appointment.pk, "symptom_pk": inversion.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, inversion
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:change_symptom_nipple_change",
                kwargs={"pk": appointment.pk, "symptom_pk": inversion.pk},
            ),
            {
                "area": [SymptomAreas.RIGHT_BREAST.value],
                "symptom_sub_type": NippleChangeChoices.INVERSION,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestAddOtherSymptomView:
    def test_renders_response(self, clinical_user_client, appointment):
        response = clinical_user_client.get(
            reverse(
                "mammograms:add_symptom_other",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:add_symptom_other",
                kwargs={"pk": appointment.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "symptom_sub_type_details": "abc",
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestChangeOtherSymptomView:
    @pytest.fixture
    def other_symptom(self, appointment):
        return SymptomFactory.create(other=True, appointment=appointment)

    def test_renders_response(self, clinical_user_client, appointment, other_symptom):
        response = clinical_user_client.get(
            reverse(
                "mammograms:change_symptom_other",
                kwargs={"pk": appointment.pk, "symptom_pk": other_symptom.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, other_symptom
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:change_symptom_other",
                kwargs={"pk": appointment.pk, "symptom_pk": other_symptom.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "symptom_sub_type_details": "abc",
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestDeleteSymptomView:
    def test_get_renders_response(self, clinical_user_client, appointment, lump):
        response = clinical_user_client.get(
            reverse(
                "mammograms:delete_symptom",
                kwargs={"pk": appointment.pk, "symptom_pk": lump.pk},
            )
        )
        assert response.status_code == 200

    def test_post_redirects_to_record_medical_information(
        self, clinical_user_client, appointment, lump
    ):
        response = clinical_user_client.post(
            reverse(
                "mammograms:delete_symptom",
                kwargs={"pk": appointment.pk, "symptom_pk": lump.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assertMessages(
            response,
            [messages.Message(level=messages.SUCCESS, message="Symptom deleted")],
        )

    def test_the_symptom_is_deleted(self, clinical_user_client, appointment, lump):
        clinical_user_client.post(
            reverse(
                "mammograms:delete_symptom",
                kwargs={"pk": appointment.pk, "symptom_pk": lump.pk},
            )
        )

        assert not Symptom.objects.filter(pk=lump.pk).exists()
