from django.urls import reverse

from manage_breast_screening.mammograms.presenters.benign_lump_history_item_presenter import (
    BenignLumpHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.breast_augmentation_history_item_presenter import (
    BreastAugmentationHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.breast_cancer_history_item_presenter import (
    BreastCancerHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.cyst_history_item_presenter import (
    CystHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.implanted_medical_device_history_item_presenter import (
    ImplantedMedicalDeviceHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.mastectomy_or_lumpectomy_history_item_presenter import (
    MastectomyOrLumpectomyHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.other_procedure_history_item_presenter import (
    OtherProcedureHistoryItemPresenter,
)
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
        self.breast_cancer_history = [
            BreastCancerHistoryItemPresenter(item)
            for item in appointment.breast_cancer_history_items.all()
        ]
        self.mastectomy_or_lumpectomy_history = [
            MastectomyOrLumpectomyHistoryItemPresenter(item)
            for item in appointment.mastectomy_or_lumpectomy_history_items.all()
        ]
        self.implanted_medical_device_history = [
            ImplantedMedicalDeviceHistoryItemPresenter(item)
            for item in appointment.implanted_medical_device_history_items.all()
        ]
        self.breast_augmentation_history = [
            BreastAugmentationHistoryItemPresenter(item)
            for item in appointment.breast_augmentation_history_items.all()
        ]
        self.other_procedure_history = [
            OtherProcedureHistoryItemPresenter(item)
            for item in appointment.other_procedure_history_items.all()
        ]
        self.benign_lump_history = [
            BenignLumpHistoryItemPresenter(item)
            for item in appointment.benign_lump_history_items.all()
        ]
        self.cyst_history = [
            CystHistoryItemPresenter(item)
            for item in appointment.cyst_history_items.all()
        ]
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

    @property
    def add_other_symptom_link(self):
        url = reverse(
            "mammograms:add_symptom_other",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": (
                "Add another symptom (other symptom)"
                if SymptomType.NIPPLE_CHANGE in self.existing_symptom_type_ids
                else "Add a symptom (other symptom)"
            ),
        }

    @property
    def add_implanted_medical_device_history_link(self):
        url = reverse(
            "mammograms:add_implanted_medical_device_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": ("Add implanted medical device history"),
        }

    @property
    def add_cyst_history_link(self):
        url = reverse(
            "mammograms:add_cyst_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": ("Add cyst history"),
        }

    @property
    def add_breast_augmentation_history_link(self):
        url = reverse(
            "mammograms:add_breast_augmentation_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": ("Add breast augmentation history"),
        }
