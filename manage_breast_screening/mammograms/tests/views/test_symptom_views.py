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
    SymptomType,
)
from manage_breast_screening.participants.tests.factories import (
    SymptomFactory,
)


@pytest.fixture
def lump(confirmed_identity_appointment):
    return SymptomFactory.create(appointment=confirmed_identity_appointment, lump=True)


@pytest.mark.django_db
class TestAddLumpView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_symptom_lump",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_symptom_lump",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "area_description_right_breast": "uiq",
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_symptom_lump",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_area">Select the location of the lump</a></li>
                    <li><a href="#id_when_started">Select how long the symptom has existed</a></li>
                    <li><a href="#id_investigated">Select whether the symptom has been investigated or not</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestUpdateLumpView:
    def test_renders_response(self, clinical_user_client, lump):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_symptom_lump",
                kwargs={"pk": lump.appointment.pk, "symptom_pk": lump.pk},
            )
        )
        assert response.status_code == 200

    def test_non_existant_or_deleted_symptom_id_is_a_404(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        """
        Note: the behaviour we probably want here is to redirect back to
        the "parent page" when a child entity is not found, and use flash
        messages to explain the error. However, none of this is
        implemented yet.
        """
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_symptom_lump",
                kwargs={
                    "pk": confirmed_identity_appointment.pk,
                    "symptom_pk": "beefbeef-beef-beef-beef-beefbeefbeef",
                },
            )
        )

        assert response.status_code == 404

    def test_different_type_of_symptom_is_a_404(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        SymptomFactory.create(
            colour_change=True, appointment=confirmed_identity_appointment
        )

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_symptom_lump",
                kwargs={
                    "pk": confirmed_identity_appointment.pk,
                    "symptom_pk": "beefbeef-beef-beef-beef-beefbeefbeef",
                },
            )
        )

        assert response.status_code == 404

    def test_valid_post_redirects_to_appointment(self, clinical_user_client, lump):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_symptom_lump",
                kwargs={"pk": lump.appointment.pk, "symptom_pk": lump.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "area_description_right_breast": "uiq",
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": lump.appointment.pk},
            ),
        )

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, lump
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_symptom_lump",
                kwargs={"pk": lump.appointment.pk, "symptom_pk": lump.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_area">Select the location of the lump</a></li>
                    <li><a href="#id_when_started">Select how long the symptom has existed</a></li>
                    <li><a href="#id_investigated">Select whether the symptom has been investigated or not</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestAddSkinChangeView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_symptom_skin_change",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_symptom_skin_change",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "area_description_right_breast": "uiq",
                "symptom_sub_type": SkinChangeChoices.DIMPLES_OR_INDENTATION,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestUpdateSkinChangeView:
    @pytest.fixture
    def colour_change(self, confirmed_identity_appointment):
        return SymptomFactory.create(
            colour_change=True, appointment=confirmed_identity_appointment
        )

    def test_renders_response(self, clinical_user_client, colour_change):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_symptom_skin_change",
                kwargs={
                    "pk": colour_change.appointment.pk,
                    "symptom_pk": colour_change.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, colour_change
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_symptom_skin_change",
                kwargs={
                    "pk": colour_change.appointment.pk,
                    "symptom_pk": colour_change.pk,
                },
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "area_description_right_breast": "uiq",
                "symptom_sub_type": SkinChangeChoices.COLOUR_CHANGE,
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": colour_change.appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestAddNippleChangeView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_symptom_nipple_change",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_symptom_nipple_change",
                kwargs={"pk": confirmed_identity_appointment.pk},
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
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestUpdateNippleChangeView:
    @pytest.fixture
    def inversion(self, confirmed_identity_appointment):
        return SymptomFactory.create(
            inversion=True, appointment=confirmed_identity_appointment
        )

    def test_renders_response(self, clinical_user_client, inversion):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_symptom_nipple_change",
                kwargs={"pk": inversion.appointment.pk, "symptom_pk": inversion.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(self, clinical_user_client, inversion):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_symptom_nipple_change",
                kwargs={"pk": inversion.appointment.pk, "symptom_pk": inversion.pk},
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
                kwargs={"pk": inversion.appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestAddOtherSymptomView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_symptom_other",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_symptom_other",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "area_description_right_breast": "uiq",
                "symptom_sub_type_details": "abc",
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestUpdateOtherSymptomView:
    @pytest.fixture
    def other_symptom(self, confirmed_identity_appointment):
        return SymptomFactory.create(
            other=True, appointment=confirmed_identity_appointment
        )

    def test_renders_response(self, clinical_user_client, other_symptom):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_symptom_other",
                kwargs={
                    "pk": other_symptom.appointment.pk,
                    "symptom_pk": other_symptom.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, other_symptom
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_symptom_other",
                kwargs={
                    "pk": other_symptom.appointment.pk,
                    "symptom_pk": other_symptom.pk,
                },
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "area_description_right_breast": "uiq",
                "symptom_sub_type_details": "abc",
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": other_symptom.appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestAddBreastPainView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_symptom_breast_pain",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_symptom_breast_pain",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "area_description_right_breast": "uiq",
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestUpdateBreastPainView:
    @pytest.fixture
    def breast_pain(self, confirmed_identity_appointment):
        return SymptomFactory.create(
            symptom_type_id=SymptomType.BREAST_PAIN,
            appointment=confirmed_identity_appointment,
        )

    def test_renders_response(self, clinical_user_client, breast_pain):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_symptom_breast_pain",
                kwargs={
                    "pk": breast_pain.appointment.pk,
                    "symptom_pk": breast_pain.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, breast_pain
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_symptom_breast_pain",
                kwargs={
                    "pk": breast_pain.appointment.pk,
                    "symptom_pk": breast_pain.pk,
                },
            ),
            {
                "area": SymptomAreas.RIGHT_BREAST.value,
                "area_description_right_breast": "uiq",
                "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS.value,
                "investigated": YesNo.NO.value,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": breast_pain.appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestDeleteSymptomView:
    def test_get_renders_response(self, clinical_user_client, lump):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:delete_symptom",
                kwargs={"pk": lump.appointment.pk, "symptom_pk": lump.pk},
            )
        )
        assert response.status_code == 200

    def test_post_redirects_to_record_medical_information(
        self, clinical_user_client, lump
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:delete_symptom",
                kwargs={"pk": lump.appointment.pk, "symptom_pk": lump.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": lump.appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message='<h3 class="nhsuk-notification-banner__heading">Symptom deleted</h3><p>Deleted lump.</p>',
                )
            ],
        )

    def test_the_symptom_is_deleted(self, clinical_user_client, lump):
        clinical_user_client.http.post(
            reverse(
                "mammograms:delete_symptom",
                kwargs={"pk": lump.appointment.pk, "symptom_pk": lump.pk},
            )
        )

        assert not Symptom.objects.filter(pk=lump.pk).exists()
