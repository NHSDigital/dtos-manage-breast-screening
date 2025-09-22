from dataclasses import dataclass

from django.urls import reverse

from manage_breast_screening.core.template_helpers import multiline_content
from manage_breast_screening.core.utils.date_formatting import format_approximate_date

from .appointment_presenters import AppointmentPresenter


class MedicalInformationPresenter:
    @dataclass
    class PresentedSymptom:
        id: str
        appointment_id: str
        symptom_type: str
        location_line: str
        started_line: str
        investigated_line: str = ""
        intermittent_line: str = ""
        stopped_line: str = ""
        additional_information_line: str = ""

        @property
        def summary_list_row(self):
            html = multiline_content(
                [
                    line
                    for line in [
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

            return {
                "key": {"text": self.symptom_type},
                "value": {"html": html},
                "actions": {
                    "items": [
                        {
                            "text": "Change",
                            "visuallyHiddenText": self.symptom_type.lower(),
                            "href": reverse(
                                "mammograms:change_symptom_lump",
                                kwargs={
                                    "pk": self.appointment_id,
                                    "lump_pk": self.id,
                                },
                            ),
                        }
                    ]
                },
            }

    def __init__(self, appointment):
        self.appointment = AppointmentPresenter(appointment)

        symptoms = appointment.symptom_set.select_related("symptom_type").order_by(
            "symptom_type__name", "reported_at"
        )
        self.symptoms = [self._present_symptom(symptom) for symptom in symptoms]

    def _present_symptom_area(self, symptom):
        return symptom.get_area_display()

    def _present_symptom(self, symptom):
        location = self._present_symptom_area(symptom)
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
            id=symptom.id,
            appointment_id=symptom.appointment_id,
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
        return [symptom.summary_list_row for symptom in self.symptoms]

    @property
    def add_lump_link(self):
        url = reverse("mammograms:add_symptom_lump", kwargs={"pk": self.appointment.pk})
        return {
            "href": url,
            "text": "Add another lump" if self.symptom_rows else "Add a lump",
        }
