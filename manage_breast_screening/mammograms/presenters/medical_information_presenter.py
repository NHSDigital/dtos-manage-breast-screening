from dataclasses import dataclass

from manage_breast_screening.core.template_helpers import multiline_content
from manage_breast_screening.core.utils.date_formatting import format_approximate_date
from manage_breast_screening.participants.models.symptom import SymptomAreas

from .appointment_presenters import AppointmentPresenter


class MedicalInformationPresenter:
    @dataclass
    class PresentedSymptom:
        symptom_type: str
        location_line: str
        started_line: str
        investigated_line: str = ""
        intermittent_line: str = ""
        stopped_line: str = ""
        additional_information_line: str = ""

    def __init__(self, appointment):
        self.appointment = AppointmentPresenter(appointment)

        symptoms = appointment.symptom_set.select_related("symptom_type").order_by(
            "symptom_type__name", "reported_at"
        )
        self.symptoms = [self._map_symptom(symptom) for symptom in symptoms]

    def _map_symptom_area(self, symptom):
        match symptom.area:
            case SymptomAreas.RIGHT_BREAST:
                return "Right breast"
            case SymptomAreas.LEFT_BREAST:
                return "Left breast"
            case SymptomAreas.BOTH_BREASTS:
                return "Both breasts"
            case _:
                return symptom.get_area_display()

    def _map_symptom(self, symptom):
        location = self._map_symptom_area(symptom)
        started = symptom.get_when_started_display()
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

        return self.PresentedSymptom(
            symptom_type=symptom.symptom_type.name,
            location_line=location,
            started_line=started,
            investigated_line=investigated,
            intermittent_line=intermittent,
            stopped_line=stopped,
            additional_information_line=additional_information,
        )

    @property
    def symptom_rows(self):
        result = []
        for symptom in self.symptoms:
            html = multiline_content(
                [
                    line
                    for line in [
                        symptom.location_line,
                        symptom.started_line,
                        symptom.investigated_line,
                        symptom.intermittent_line,
                        symptom.stopped_line,
                        symptom.additional_information_line,
                    ]
                    if line
                ]
            )

            result.append(
                {
                    "key": {"text": symptom.symptom_type},
                    "value": {"html": html},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "visuallyHiddenText": symptom.symptom_type.lower(),
                                "href": "#",
                            }
                        ]
                    },
                }
            )
        return result
