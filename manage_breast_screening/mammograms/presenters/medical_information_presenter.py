from django.urls import reverse

from manage_breast_screening.mammograms.presenters.symptom_presenter import (
    SymptomPresenter,
)
from manage_breast_screening.participants.models.symptom import SymptomType

from .appointment_presenters import AppointmentPresenter


class MedicalInformationPresenter:
    def __init__(self, appointment):
        self.appointment = AppointmentPresenter(appointment)

        symptoms = appointment.symptom_set.select_related("symptom_type").order_by(
            "symptom_type__name", "reported_at"
        )
        self.symptoms = [SymptomPresenter(symptom) for symptom in symptoms]
        self.existing_symptom_type_ids = {
            symptom.symptom_type_id for symptom in symptoms
        }

    @property
    def symptom_rows(self):
        return [symptom.summary_list_row for symptom in self.symptoms]

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
