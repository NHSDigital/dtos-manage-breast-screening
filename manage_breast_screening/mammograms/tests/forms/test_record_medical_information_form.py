import pytest

from manage_breast_screening.mammograms.forms import RecordMedicalInformationForm
from manage_breast_screening.participants.models import MedicalInformationSection
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestRecordMedicalInformationForm:
    def test_save_creates_reviews_for_all_missing_sections(self, clinical_user):
        appointment = AppointmentFactory.create()

        assert appointment.medical_information_reviews.count() == 0

        form = RecordMedicalInformationForm(
            appointment=appointment,
            user=clinical_user,
        )
        form.save()

        assert appointment.medical_information_reviews.count() == 5
        all_sections = {choice[0] for choice in MedicalInformationSection.choices}
        reviewed_sections = set(
            appointment.medical_information_reviews.values_list("section", flat=True)
        )
        assert reviewed_sections == all_sections
        for review in appointment.medical_information_reviews.all():
            assert review.reviewed_by == clinical_user

    def test_save_does_nothing_when_all_sections_already_reviewed(
        self, clinical_user, django_assert_num_queries
    ):
        appointment = AppointmentFactory.create()

        for section, _ in MedicalInformationSection.choices:
            appointment.medical_information_reviews.create(
                section=section,
                reviewed_by=clinical_user,
            )

        assert appointment.medical_information_reviews.count() == 5

        form = RecordMedicalInformationForm(
            appointment=appointment,
            user=clinical_user,
        )
        form.save()

        assert appointment.medical_information_reviews.count() == 5
