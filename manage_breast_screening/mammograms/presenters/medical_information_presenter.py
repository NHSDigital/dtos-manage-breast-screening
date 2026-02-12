from urllib.parse import quote

from django.urls import reverse

from manage_breast_screening.mammograms.presenters.medical_history.benign_lump_history_item_presenter import (
    BenignLumpHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.medical_history.breast_augmentation_history_item_presenter import (
    BreastAugmentationHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.medical_history.breast_cancer_history_item_presenter import (
    BreastCancerHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.medical_history.cyst_history_item_presenter import (
    CystHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.medical_history.implanted_medical_device_history_item_presenter import (
    ImplantedMedicalDeviceHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.medical_history.mastectomy_or_lumpectomy_history_item_presenter import (
    MastectomyOrLumpectomyHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.medical_history.other_procedure_history_item_presenter import (
    OtherProcedureHistoryItemPresenter,
)
from manage_breast_screening.mammograms.presenters.symptom_presenter import (
    SymptomPresenter,
)
from manage_breast_screening.participants.models import MedicalInformationSection

from .appointment_presenters import AppointmentPresenter

# Section order for "Next section" navigation
SECTION_ORDER = {
    MedicalInformationSection.MAMMOGRAM_HISTORY: MedicalInformationSection.SYMPTOMS,
    MedicalInformationSection.SYMPTOMS: MedicalInformationSection.MEDICAL_HISTORY,
    MedicalInformationSection.MEDICAL_HISTORY: MedicalInformationSection.BREAST_FEATURES,
    MedicalInformationSection.BREAST_FEATURES: MedicalInformationSection.OTHER_INFORMATION,
    MedicalInformationSection.OTHER_INFORMATION: MedicalInformationSection.OTHER_INFORMATION,
}

# Section IDs for anchor navigation
SECTION_ANCHORS = {
    MedicalInformationSection.MAMMOGRAM_HISTORY: "mammogram-history",
    MedicalInformationSection.SYMPTOMS: "symptoms",
    MedicalInformationSection.MEDICAL_HISTORY: "medical-history",
    MedicalInformationSection.BREAST_FEATURES: "breast-features",
    MedicalInformationSection.OTHER_INFORMATION: "other-information",
}


class MedicalInformationPresenter:
    def __init__(self, appointment):
        self.appointment = AppointmentPresenter(appointment)
        symptoms = appointment.symptoms.select_related("symptom_type").order_by(
            "symptom_type__name", "reported_at"
        )
        self.symptoms = [SymptomPresenter(symptom) for symptom in symptoms]

        self.breast_cancer_history = self._present_items(
            appointment.breast_cancer_history_items.all(),
            BreastCancerHistoryItemPresenter,
        )

        self.mastectomy_or_lumpectomy_history = self._present_items(
            appointment.mastectomy_or_lumpectomy_history_items.all(),
            MastectomyOrLumpectomyHistoryItemPresenter,
        )

        self.implanted_medical_device_history = self._present_items(
            appointment.implanted_medical_device_history_items.all(),
            ImplantedMedicalDeviceHistoryItemPresenter,
        )

        self.breast_augmentation_history = self._present_items(
            appointment.breast_augmentation_history_items.all(),
            BreastAugmentationHistoryItemPresenter,
        )

        self.other_procedure_history = self._present_items(
            appointment.other_procedure_history_items.all(),
            OtherProcedureHistoryItemPresenter,
        )

        self.benign_lump_history = self._present_items(
            appointment.benign_lump_history_items.all(), BenignLumpHistoryItemPresenter
        )

        self.cyst_history = self._present_items(
            appointment.cyst_history_items.all(), CystHistoryItemPresenter
        )

        self.existing_symptom_type_ids = {
            symptom.symptom_type_id for symptom in symptoms
        }

        self._section_reviews = {
            review.section: review
            for review in appointment.medical_information_reviews.all()
        }

        self.hormone_replacement_therapy = getattr(
            appointment, "hormone_replacement_therapy", None
        )

        self.pregnancy_and_breastfeeding = getattr(
            appointment, "pregnancy_and_breastfeeding", None
        )

    @property
    def symptom_rows(self):
        return [symptom.summary_list_row for symptom in self.symptoms]

    @property
    def read_only_symptom_rows(self):
        return [
            symptom.build_summary_list_row(include_actions=False)
            for symptom in self.symptoms
        ]

    @property
    def symptom_buttons(self):
        return [
            self.add_lump_button,
            self.add_swelling_or_shape_change_button,
            self.add_skin_change_button,
            self.add_nipple_change_button,
            self.add_other_symptom_button,
        ]

    @property
    def any_medical_history(self):
        return any(
            (
                self.benign_lump_history,
                self.breast_augmentation_history,
                self.breast_cancer_history,
                self.cyst_history,
                self.implanted_medical_device_history,
                self.mastectomy_or_lumpectomy_history,
                self.other_procedure_history,
            )
        )

    @property
    def medical_history_buttons(self):
        return [
            self.add_breast_cancer_history_button,
            self.add_implanted_medical_device_history_button,
            self.add_breast_augmentation_history_button,
            self.add_mastectomy_or_lumpectomy_history_button,
            self.add_cyst_history_button,
            self.add_benign_lump_history_button,
            self.add_other_procedure_history_button,
        ]

    @property
    def add_lump_button(self):
        url = reverse("mammograms:add_symptom_lump", kwargs={"pk": self.appointment.pk})

        return {"href": url, "text": "Lump"}

    @property
    def add_swelling_or_shape_change_button(self):
        url = reverse(
            "mammograms:add_symptom_swelling_or_shape_change",
            kwargs={"pk": self.appointment.pk},
        )

        return {"href": url, "text": "Swelling or shape change"}

    @property
    def add_skin_change_button(self):
        url = reverse(
            "mammograms:add_symptom_skin_change",
            kwargs={"pk": self.appointment.pk},
        )

        return {"href": url, "text": "Skin change"}

    @property
    def add_nipple_change_button(self):
        url = reverse(
            "mammograms:add_symptom_nipple_change",
            kwargs={"pk": self.appointment.pk},
        )

        return {"href": url, "text": "Nipple change"}

    @property
    def add_other_symptom_button(self):
        url = reverse(
            "mammograms:add_symptom_other",
            kwargs={"pk": self.appointment.pk},
        )

        return {"href": url, "text": "Other"}

    @property
    def add_breast_cancer_history_button(self):
        url = reverse(
            "mammograms:add_breast_cancer_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": "Breast cancer",
        }

    @property
    def add_implanted_medical_device_history_button(self):
        url = reverse(
            "mammograms:add_implanted_medical_device_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": "Implanted medical device",
        }

    @property
    def add_cyst_history_button(self):
        if self.cyst_history:
            return None

        url = reverse(
            "mammograms:add_cyst_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": ("Cysts"),
        }

    @property
    def add_breast_augmentation_history_button(self):
        if self.breast_augmentation_history:
            return None

        url = reverse(
            "mammograms:add_breast_augmentation_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": "Breast implants or augmentation",
        }

    @property
    def add_benign_lump_history_button(self):
        url = reverse(
            "mammograms:add_benign_lump_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": "Benign lumps",
        }

    @property
    def add_mastectomy_or_lumpectomy_history_button(self):
        url = reverse(
            "mammograms:add_mastectomy_or_lumpectomy_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": "Mastectomy or lumpectomy",
        }

    @property
    def add_other_procedure_history_button(self):
        url = reverse(
            "mammograms:add_other_procedure_history_item",
            kwargs={"pk": self.appointment.pk},
        )

        return {
            "href": url,
            "text": "Other procedures",
        }

    @property
    def medical_information_url(self):
        return reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )

    @property
    def add_mammogram_button(self):
        url = (
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": self.appointment.pk},
            )
            + "?return_url="
            + quote(self.medical_information_url)
        )

        return {"href": url, "text": "Add another mammogram"}

    def _present_items(self, items, presenter_class):
        items = list(items)
        if len(items) == 1:
            return [presenter_class(items[0])]
        else:
            return [
                presenter_class(item, counter=counter)
                for counter, item in enumerate(items, 1)
            ]

    def get_anchor(self, section):
        return SECTION_ANCHORS.get(section)

    def is_section_reviewed(self, section):
        return section in self._section_reviews

    def review_status_tag_properties(self, section):
        if self.is_section_reviewed(section):
            return {
                "text": "Reviewed",
                "classes": "nhsuk-tag--green app-section-review-tag",
            }
        else:
            return {
                "text": "To review",
                "classes": "nhsuk-tag--blue app-section-review-tag",
            }

    def review_action_button_properties(self, section):
        if self.is_section_reviewed(section):
            next_section = SECTION_ORDER.get(section)
            anchor = SECTION_ANCHORS.get(next_section)
            return {
                "href": f"#{anchor}",
                "text": "Next section",
                "is_anchor": True,
            }
        else:
            url = reverse(
                "mammograms:mark_section_reviewed",
                kwargs={
                    "pk": self.appointment.pk,
                    "section": section,
                },
            )
            return {
                "href": url,
                "text": "Mark as reviewed",
                "is_anchor": False,
            }

    @property
    def add_hormone_replacement_therapy_link(self):
        return reverse(
            "mammograms:add_hormone_replacement_therapy",
            kwargs={"pk": self.appointment.pk},
        )

    def hormone_replacement_therapy_actions(self, read_only=False):
        return (
            {
                "items": [
                    {
                        "href": reverse(
                            "mammograms:change_hormone_replacement_therapy",
                            kwargs={
                                "pk": self.appointment.pk,
                                "hrt_pk": self.hormone_replacement_therapy.pk,
                            },
                        ),
                        "text": "Change",
                        "visuallyHiddenText": "hormone replacement therapy",
                        "classes": "nhsuk-link--no-visited-state",
                    },
                ],
            }
            if self.hormone_replacement_therapy and not read_only
            else None
        )

    @property
    def add_pregnancy_and_breastfeeding_link(self):
        return reverse(
            "mammograms:add_pregnancy_and_breastfeeding",
            kwargs={"pk": self.appointment.pk},
        )

    def pregnancy_and_breastfeeding_actions(self, read_only=False):
        return (
            {
                "items": [
                    {
                        "href": reverse(
                            "mammograms:change_pregnancy_and_breastfeeding",
                            kwargs={
                                "pk": self.appointment.pk,
                                "pab_pk": self.pregnancy_and_breastfeeding.pk,
                            },
                        ),
                        "text": "Change",
                        "visuallyHiddenText": "pregnancy and breastfeeding",
                        "classes": "nhsuk-link--no-visited-state",
                    },
                ],
            }
            if self.pregnancy_and_breastfeeding and not read_only
            else None
        )
