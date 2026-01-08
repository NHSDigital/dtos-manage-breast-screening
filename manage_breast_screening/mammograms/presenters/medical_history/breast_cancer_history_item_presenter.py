from django.urls import reverse

from manage_breast_screening.core.template_helpers import nl2br
from manage_breast_screening.core.utils.date_formatting import format_year_with_relative
from manage_breast_screening.participants.models.medical_history.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)


class BreastCancerHistoryItemPresenter:
    def __init__(self, breast_cancer_history_item, counter=None):
        self._item = breast_cancer_history_item
        self.counter = counter

        self.cancer_location = self._item.get_diagnosis_location_display()

        self.right_breast_procedure = self._item.get_right_breast_procedure_display()
        self.left_breast_procedure = self._item.get_left_breast_procedure_display()

        self.diagnosis_year = format_year_with_relative(self._item.diagnosis_year)

        self.right_breast_other_surgery = [
            BreastCancerHistoryItem.Surgery(choice).label
            for choice in self._item.right_breast_other_surgery
        ]
        self.left_breast_other_surgery = [
            BreastCancerHistoryItem.Surgery(choice).label
            for choice in self._item.left_breast_other_surgery
        ]

        self.right_breast_treatments = [
            BreastCancerHistoryItem.Treatment(choice).label
            for choice in self._item.right_breast_treatment
        ]
        self.left_breast_treatments = [
            BreastCancerHistoryItem.Treatment(choice).label
            for choice in self._item.left_breast_treatment
        ]

        self.systemic_treatments = [
            BreastCancerHistoryItem.SystemicTreatment(choice).label
            for choice in self._item.systemic_treatments
        ]

        self.additional_details = nl2br(self._item.additional_details)

    @property
    def change_link(self):
        return {
            "href": reverse(
                "mammograms:change_breast_cancer_history_item",
                kwargs={
                    "pk": self._item.appointment_id,
                    "history_item_pk": self._item.pk,
                },
            ),
            "text": "Change",
            "visually_hidden_text": (
                f" breast cancer item {self.counter}"
                if self.counter
                else " breast cancer item"
            ),
        }

    @property
    def intervention_location(self):
        return {
            "type": self._item.get_intervention_location_display(),
            "details": self._item.intervention_location_details,
        }
