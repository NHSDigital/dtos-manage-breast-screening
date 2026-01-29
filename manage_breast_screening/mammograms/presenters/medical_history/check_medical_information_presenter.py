from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.models.medical_history.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)
from manage_breast_screening.participants.models.medical_history.other_procedure_history_item import (
    OtherProcedureHistoryItem,
)
from manage_breast_screening.participants.models.symptom import (
    NippleChangeChoices,
    SkinChangeChoices,
    SymptomAreas,
    SymptomType,
)


class CheckMedicalInformationPresenter:
    def __init__(self, appointment):
        previous_mammograms_count = appointment.reported_mammograms.count()
        self.previous_mammograms = (
            "No additional mammograms added"
            if previous_mammograms_count == 0
            else f"{previous_mammograms_count} additional mammograms added"
        )

        self.symptoms = self.format_symptoms(appointment)

        self.medical_history = []
        self.medical_history.extend(self.format_breast_cancer(appointment))
        self.medical_history.extend(self.format_implanted_medical_devices(appointment))
        self.medical_history.extend(self.format_breast_augmentation(appointment))
        self.medical_history.extend(self.format_mastectomy_or_lumpectomy(appointment))
        self.medical_history.extend(self.format_cysts(appointment))
        self.medical_history.extend(self.format_benign_lump(appointment))
        self.medical_history.extend(self.format_other_procedure(appointment))

    def format_breast_cancer(self, appointment):
        result = []
        for item in appointment.breast_cancer_history_items.all():
            summary = "Breast cancer" + self.format_year(item.diagnosis_year)
            result.append(summary)
        return result

    def format_implanted_medical_devices(self, appointment):
        result = []
        for item in appointment.implanted_medical_device_history_items.all():
            summary = (
                "Implanted "
                + self.get_implanted_device_display(item)
                + self.format_procedure_and_removal_years(
                    item, item.device_has_been_removed
                )
            )
            result.append(summary)
        return result

    def get_implanted_device_display(self, item):
        match item.device:
            case ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE:
                return "cardiac device"
            case ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE:
                return "other medical device"
            case ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE:
                return "Hickman line"
            case _:
                raise ValueError(f"Unknown device type: {item.device}")

    def format_breast_augmentation(self, appointment):
        result = []
        for item in appointment.breast_augmentation_history_items.all():
            procedures = set(item.right_breast_procedures + item.left_breast_procedures)

            had_implants = (
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS.value
                in procedures
            )

            had_augmentation = (
                BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION.value
                in procedures
            )

            if had_implants and had_augmentation:
                procedure_type = "Breast implants and augmentation"
            elif had_implants:
                procedure_type = "Breast implants"
            elif had_augmentation:
                procedure_type = "Breast augmentation"
            else:
                procedure_type = "No procedures"

            summary = procedure_type + self.format_procedure_and_removal_years(
                item, item.implants_have_been_removed
            )
            result.append(summary)
        return result

    def format_mastectomy_or_lumpectomy(self, appointment):
        result = []
        for item in appointment.mastectomy_or_lumpectomy_history_items.all():
            right_breast_procedure = item.right_breast_procedure
            left_breast_procedure = item.left_breast_procedure

            had_implants = self.is_mastectomy(
                right_breast_procedure
            ) or self.is_mastectomy(left_breast_procedure)

            had_lumpectomy = self.is_lumpectomy(
                right_breast_procedure
            ) or self.is_lumpectomy(left_breast_procedure)

            if had_implants and had_lumpectomy:
                procedure_type = "Mastectomy and lumpectomy"
            elif had_implants:
                procedure_type = "Mastectomy"
            elif had_lumpectomy:
                procedure_type = "Lumpectomy"
            else:
                procedure_type = "No procedure"

            summary = (
                f"{procedure_type} ({item.year_of_surgery})"
                if item.year_of_surgery
                else procedure_type
            )
            result.append(summary)
        return result

    def is_mastectomy(self, item):
        return (
            item
            == MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING.value
            or item
            == MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING.value
        )

    def is_lumpectomy(self, item):
        return item == MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY.value

    def format_cysts(self, appointment):
        return ["History of cysts"] if appointment.cyst_history_items.exists() else []

    def format_benign_lump(self, appointment):
        result = []
        for item in appointment.benign_lump_history_items.all():
            summary = "Benign lumps" + self.format_year(item.procedure_year)
            result.append(summary)
        return result

    def format_other_procedure(self, appointment):
        result = []
        for item in appointment.other_procedure_history_items.all():
            summary = "Other procedures ("

            if item.procedure == OtherProcedureHistoryItem.Procedure.OTHER:
                summary += item.procedure_details
            else:
                summary += item.get_procedure_display().lower()

            if item.procedure_year:
                summary += f", {item.procedure_year}"

            summary += ")"

            result.append(summary)
        return result

    def format_symptoms(self, appointment):
        symptoms = appointment.symptoms.select_related("symptom_type").order_by(
            "symptom_type__name", "reported_at"
        )

        result = []
        for item in symptoms:
            summary = self.summarise_symptom(item)
            result.append(summary)
        return result

    def summarise_symptom(self, symptom):
        summary = self.format_symptom_type(symptom)

        # Add sub-type details for specific symptom types
        if symptom.symptom_type.id == SymptomType.NIPPLE_CHANGE:
            if symptom.symptom_sub_type.id == NippleChangeChoices.OTHER:
                change_type = symptom.symptom_sub_type_details
            else:
                change_type = self.format_symptom_sub_type(symptom)
            summary += f": {change_type}"
        elif symptom.symptom_type.id == SymptomType.SKIN_CHANGE:
            if symptom.symptom_sub_type.id == SkinChangeChoices.OTHER:
                change_type = symptom.symptom_sub_type_details
            else:
                change_type = self.format_symptom_sub_type(symptom)
            summary += f": {change_type}"
        elif symptom.symptom_type.id == SymptomType.OTHER:
            summary = symptom.symptom_sub_type_details

        # Add location
        location = ""
        if symptom.symptom_type.id == SymptomType.NIPPLE_CHANGE:
            if symptom.area == SymptomAreas.BOTH_BREASTS:
                location = "both nipples"
            elif symptom.area == SymptomAreas.RIGHT_BREAST:
                location = "right nipple"
            elif symptom.area == SymptomAreas.LEFT_BREAST:
                location = "left nipple"
        elif symptom.area:
            location = symptom.get_area_display().lower()

        if location:
            summary += f" ({location})"

        return summary

    def format_symptom_type(self, symptom):
        id = symptom.symptom_type.id
        return id[0].upper() + id[1:].lower().replace("_", " ")

    def format_symptom_sub_type(self, symptom):
        return symptom.symptom_sub_type.name.lower()

    def format_procedure_and_removal_years(self, item, has_been_removed):
        summary = ""
        if has_been_removed:
            if item.procedure_year:
                summary += f" ({item.procedure_year}, removed"
                if item.removal_year:
                    summary += f" {item.removal_year}"
                summary += ")"
            else:
                summary += " (removed"
                if item.removal_year:
                    summary += f" {item.removal_year}"
                summary += ")"
        elif item.procedure_year:
            summary += f" ({item.procedure_year})"
        return summary

    def format_year(self, year):
        return f" ({year})" if year else " (year unknown)"
