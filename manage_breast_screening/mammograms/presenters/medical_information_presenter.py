from dataclasses import dataclass

from django.urls import reverse

from manage_breast_screening.core.template_helpers import multiline_content
from manage_breast_screening.core.utils.date_formatting import format_approximate_date
from manage_breast_screening.participants.models.symptom import (
    NippleChangeChoices,
    RelativeDateChoices,
    SkinChangeChoices,
    SymptomAreas,
    SymptomType,
)

from .appointment_presenters import AppointmentPresenter


@dataclass
class PresentedSymptom:
    id: str
    appointment_id: str
    symptom_type_id: str
    symptom_type_name: str
    location_line: str
    started_line: str
    change_type_line: str = ""
    investigated_line: str = ""
    intermittent_line: str = ""
    stopped_line: str = ""
    additional_information_line: str = ""

    @staticmethod
    def _present_symptom_area(symptom):
        if symptom.area == SymptomAreas.OTHER and symptom.area_description:
            location = f"Other: {symptom.area_description}"
        else:
            location = symptom.get_area_display()
        return location

    @staticmethod
    def _present_started(symptom):
        match symptom.when_started:
            case RelativeDateChoices.SINCE_A_SPECIFIC_DATE:
                if symptom.year_started is None or symptom.month_started is None:
                    # Shouldn't happen unless there is a bug in data entry
                    return "Since a specific date"

                return format_approximate_date(
                    symptom.year_started, symptom.month_started
                )
            case RelativeDateChoices.NOT_SURE:
                return "Not sure"
            case _:
                return symptom.get_when_started_display() + " ago"

    @classmethod
    def from_symptom(cls, symptom):
        location = cls._present_symptom_area(symptom)
        started = cls._present_started(symptom)
        if symptom.year_started is not None and symptom.month_started is not None:
            started = format_approximate_date(
                symptom.year_started, symptom.month_started
            )

        investigated = (
            f"Previously investigated: {symptom.investigation_details}"
            if symptom.investigated
            else "Not investigated"
        )

        intermittent = "Symptom is intermittent" if symptom.intermittent else ""
        stopped = f"Stopped: {symptom.when_resolved}" if symptom.when_resolved else ""

        additional_information = (
            f"Additional information: {symptom.additional_information}"
            if symptom.additional_information
            else ""
        )

        change_type_line = ""
        if symptom.symptom_type_id in [
            SymptomType.SKIN_CHANGE,
            SymptomType.NIPPLE_CHANGE,
        ]:
            if (
                symptom.symptom_sub_type_id
                in [SkinChangeChoices.OTHER, NippleChangeChoices.OTHER]
                and symptom.symptom_sub_type_details
            ):
                change_type_line = f"Change type: {symptom.symptom_sub_type_details}"
            else:
                change_type_line = (
                    f"Change type: {symptom.symptom_sub_type.name.lower()}"
                )

        return cls(
            id=symptom.id,
            appointment_id=symptom.appointment_id,
            symptom_type_id=symptom.symptom_type_id,
            symptom_type_name=symptom.symptom_type.name,
            location_line=location,
            change_type_line=change_type_line,
            started_line=started,
            investigated_line=investigated,
            intermittent_line=intermittent,
            stopped_line=stopped,
            additional_information_line=additional_information,
        )

    def change_view(self):
        match self.symptom_type_id:
            case SymptomType.LUMP:
                return "mammograms:change_symptom_lump"
            case SymptomType.SWELLING_OR_SHAPE_CHANGE:
                return "mammograms:change_symptom_swelling_or_shape_change"
            case SymptomType.SKIN_CHANGE:
                return "mammograms:change_symptom_skin_change"
            case SymptomType.NIPPLE_CHANGE:
                return "mammograms:change_symptom_nipple_change"
            case _:
                raise ValueError(self.symptom_type_id)

    @property
    def summary_list_row(self):
        return self.build_summary_list_row()

    def build_summary_list_row(self, include_actions=True):
        html = multiline_content(
            [
                line
                for line in [
                    self.change_type_line,
                    self.location_line,
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
            "key": {"text": self.symptom_type_name},
            "value": {"html": html},
        }

        if include_actions:
            result["actions"] = {
                "items": [
                    {
                        "text": "Change",
                        "visuallyHiddenText": self.symptom_type_name.lower(),
                        "href": reverse(
                            self.change_view(),
                            kwargs={
                                "pk": self.appointment_id,
                                "symptom_pk": self.id,
                            },
                        ),
                    }
                ]
            }

        return result


class MedicalInformationPresenter:
    def __init__(self, appointment):
        self.appointment = AppointmentPresenter(appointment)

        symptoms = appointment.symptom_set.select_related("symptom_type").order_by(
            "symptom_type__name", "reported_at"
        )
        self.symptoms = [PresentedSymptom.from_symptom(symptom) for symptom in symptoms]

    @property
    def symptom_rows(self):
        return [symptom.summary_list_row for symptom in self.symptoms]

    @property
    def existing_symptom_type_ids(self):
        return {symptom.symptom_type_id for symptom in self.symptoms}

    @property
    def add_lump_link(self):
        url = reverse("mammograms:add_symptom_lump", kwargs={"pk": self.appointment.pk})

        return {
            "href": url,
            "text": (
                "Add another lump"
                if SymptomType.LUMP in self.existing_symptom_type_ids
                else "Add a lump"
            ),
        }

    @property
    def add_swelling_or_shape_change_link(self):
        url = reverse(
            "mammograms:add_symptom_swelling_or_shape_change",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": (
                "Add another swelling or shape change"
                if SymptomType.SWELLING_OR_SHAPE_CHANGE
                in self.existing_symptom_type_ids
                else "Add a swelling or shape change"
            ),
        }

    @property
    def add_skin_change_link(self):
        url = reverse(
            "mammograms:add_symptom_skin_change",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": (
                "Add another skin change"
                if SymptomType.SKIN_CHANGE in self.existing_symptom_type_ids
                else "Add a skin change"
            ),
        }

    @property
    def add_nipple_change_link(self):
        url = reverse(
            "mammograms:add_symptom_nipple_change",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": (
                "Add another nipple change"
                if SymptomType.NIPPLE_CHANGE in self.existing_symptom_type_ids
                else "Add a nipple change"
            ),
        }
