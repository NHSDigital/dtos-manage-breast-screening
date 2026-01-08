from django.urls import reverse

from manage_breast_screening.core.template_helpers import nl2br
from manage_breast_screening.core.utils.date_formatting import format_year_with_relative


class OtherProcedureHistoryItemPresenter:
    def __init__(self, other_procedure_history_item, counter=None):
        self._item = other_procedure_history_item
        self.counter = counter

        self.procedure = self._item.get_procedure_display()
        self.procedure_details = self._item.procedure_details or "N/A"
        self.procedure_year = format_year_with_relative(self._item.procedure_year)
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def procedure_with_details(self):
        return f"{self.procedure}: {self.procedure_details}"

    @property
    def type(self):
        return {"type": self.procedure, "details": self.procedure_details}

    @property
    def summary_list_params(self):
        # This is a placeholder until we have a properly formatted table.
        return {
            "rows": [
                {
                    "key": {"text": "Procedure"},
                    "value": {"html": self.procedure},
                },
                {
                    "key": {"text": "Procedure details"},
                    "value": {"html": self.procedure_details},
                },
                {
                    "key": {"text": "Procedure year"},
                    "value": {"html": self.procedure_year},
                },
                {
                    "key": {"text": "Additional details"},
                    "value": {"html": self.additional_details},
                },
            ],
        }

    @property
    def change_link(self):
        return {
            "href": reverse(
                "mammograms:change_other_procedure_history_item",
                kwargs={
                    "pk": self._item.appointment_id,
                    "history_item_pk": self._item.pk,
                },
            ),
            "text": "Change",
            "visually_hidden_text": (
                f" other procedure item {self.counter}"
                if self.counter
                else " other procedure item"
            ),
        }
