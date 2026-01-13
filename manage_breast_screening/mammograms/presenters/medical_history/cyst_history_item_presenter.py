from django.urls import reverse

from manage_breast_screening.core.template_helpers import nl2br


class CystHistoryItemPresenter:
    def __init__(self, breast_cancer_history_item, counter=None):
        self._item = breast_cancer_history_item

        # If there are more than one of these items, we add a counter to the
        # visually hidden text
        self.counter = counter

        self.treatment = self._item.get_treatment_display()
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def change_link(self):
        return {
            "href": reverse(
                "mammograms:change_cyst_history_item",
                kwargs={
                    "pk": self._item.appointment_id,
                    "history_item_pk": self._item.pk,
                },
            ),
            "text": "Change",
            "visually_hidden_text": (
                f" cyst item {self.counter}" if self.counter else " cyst item"
            ),
        }
