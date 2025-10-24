from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from manage_breast_screening.core.template_helpers import (
    message_with_heading,
    multiline_content,
)
from manage_breast_screening.core.utils.date_formatting import format_approximate_date
from manage_breast_screening.participants.models.symptom import (
    NippleChangeChoices,
    RelativeDateChoices,
    SkinChangeChoices,
    SymptomAreas,
    SymptomType,
)


class SymptomPresenter:
    def __init__(self, symptom):
        self._symptom = symptom

    @property
    def area_line(self):
        if self._symptom.area == SymptomAreas.OTHER and self._symptom.area_description:
            return f"Other: {self._symptom.area_description}"
        else:
            return self._symptom.get_area_display()

    @property
    def change_type_line(self):
        type_id = self._symptom.symptom_type_id
        sub_type_id = self._symptom.symptom_sub_type_id
        sub_type_details = self._symptom.symptom_sub_type_details

        # fmt: off
        match (type_id, sub_type_id, sub_type_details):
            case (
                [SymptomType.SKIN_CHANGE, SkinChangeChoices.OTHER, details] |
                [SymptomType.NIPPLE_CHANGE, NippleChangeChoices.OTHER, details]
            ) if details:
                return f"Change type: {details}"
            case [SymptomType.SKIN_CHANGE, _, _] | [SymptomType.NIPPLE_CHANGE, _, _]:
                return f"Change type: {self._symptom.symptom_sub_type.name.lower()}"
            case [SymptomType.OTHER, _, description] if description:
                return f"Description: {description}"
            case _:
                return ""
        # fmt: on

    @property
    def type_name(self):
        """
        A way of refering to the specific symptom type
        """
        if self._symptom.symptom_type_id == SymptomType.OTHER:
            return "other symptom"
        else:
            return self._symptom.symptom_type.name.lower()

    @property
    def name(self):
        """
        A way of referring to a symptom within a sentence
        """
        result = self.type_name

        if self.change_type_line:
            details = self.change_type_line[0].lower() + self.change_type_line[1:]
            result += f" ({details})"

        return result

    @property
    def started_line(self):
        match self._symptom.when_started:
            case RelativeDateChoices.SINCE_A_SPECIFIC_DATE:
                if (
                    self._symptom.year_started is None
                    or self._symptom.month_started is None
                ):
                    # Shouldn't happen unless there is a bug in data entry
                    return "Since a specific date"

                return format_approximate_date(
                    self._symptom.year_started, self._symptom.month_started
                )
            case RelativeDateChoices.NOT_SURE:
                return "Not sure"
            case _:
                return self._symptom.get_when_started_display() + " ago"

    @property
    def investigated_line(self):
        return (
            f"Previously investigated: {self._symptom.investigation_details}"
            if self._symptom.investigated
            else "Not investigated"
        )

    @property
    def intermittent_line(self):
        return "Symptom is intermittent" if self._symptom.intermittent else ""

    @property
    def stopped_line(self):
        return (
            f"Stopped: {self._symptom.when_resolved}"
            if self._symptom.when_resolved
            else ""
        )

    @property
    def additional_information_line(self):
        return (
            f"Additional information: {self._symptom.additional_information}"
            if self._symptom.additional_information
            else ""
        )

    @property
    def summary_list_row(self):
        return self.build_summary_list_row()

    def build_summary_list_row(self, include_actions=True):
        html = multiline_content(
            [
                line
                for line in [
                    self.change_type_line,
                    self.area_line,
                    self.started_line,
                    self.investigated_line,
                    self.intermittent_line,
                    self.stopped_line,
                    self.additional_information_line,
                ]
                if line
            ]
        )

        result = {
            "key": {"text": self._symptom.symptom_type.name},
            "value": {"html": html},
        }

        if include_actions:
            result["actions"] = {
                "items": [
                    {
                        "text": "Change",
                        "visuallyHiddenText": self._symptom.symptom_type.name.lower(),
                        "href": reverse(
                            self.change_view(),
                            kwargs={
                                "pk": self._symptom.appointment_id,
                                "symptom_pk": self._symptom.id,
                            },
                        ),
                    }
                ]
            }

        return result

    def change_view(self):
        match self._symptom.symptom_type_id:
            case SymptomType.LUMP:
                return "mammograms:change_symptom_lump"
            case SymptomType.SWELLING_OR_SHAPE_CHANGE:
                return "mammograms:change_symptom_swelling_or_shape_change"
            case SymptomType.SKIN_CHANGE:
                return "mammograms:change_symptom_skin_change"
            case SymptomType.NIPPLE_CHANGE:
                return "mammograms:change_symptom_nipple_change"
            case _:
                return "mammograms:change_symptom_other"

    @property
    def delete_message_html(self):
        return message_with_heading(
            heading="Symptom deleted",
            html=mark_safe(f"<p>Deleted {escape(self.name)}.</p>"),
        )

    @property
    def add_message_html(self):
        return message_with_heading(
            heading="Symptom added",
            html=mark_safe(f"<p>Added {escape(self.name)}.</p>"),
        )
