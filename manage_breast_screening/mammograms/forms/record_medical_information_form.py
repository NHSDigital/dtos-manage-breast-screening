from django import forms

from manage_breast_screening.participants.models import MedicalInformationSection
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)


class RecordMedicalInformationForm(forms.Form):
    def __init__(self, *args, appointment, user, **kwargs):
        self.appointment = appointment
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self):
        all_sections = [choice[0] for choice in MedicalInformationSection.choices]
        reviewed_sections = set(
            self.appointment.medical_information_reviews.values_list(
                "section", flat=True
            )
        )
        missing_sections = set(all_sections) - reviewed_sections

        for section in missing_sections:
            self.appointment.medical_information_reviews.create(
                section=section,
                reviewed_by=self.user,
            )

        self.appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION,
            created_by=self.user,
        )
