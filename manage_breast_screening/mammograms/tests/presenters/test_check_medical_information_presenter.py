import pytest

from manage_breast_screening.mammograms.presenters.medical_history.check_medical_information_presenter import (
    CheckMedicalInformationPresenter,
)
from manage_breast_screening.participants.models.medical_history.benign_lump_history_item import (
    BenignLumpHistoryItem,
)
from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)
from manage_breast_screening.participants.models.medical_history.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)
from manage_breast_screening.participants.models.medical_history.cyst_history_item import (
    CystHistoryItem,
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
from manage_breast_screening.participants.models.other_information.hormone_replacement_therapy import (
    HormoneReplacementTherapy,
)
from manage_breast_screening.participants.models.other_information.pregnancy_and_breastfeeding import (
    PregnancyAndBreastfeeding,
)
from manage_breast_screening.participants.models.symptom import (
    NippleChangeChoices,
    RelativeDateChoices,
    SkinChangeChoices,
    SymptomAreas,
    SymptomType,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BenignLumpHistoryItemFactory,
    BreastAugmentationHistoryItemFactory,
    BreastCancerHistoryItemFactory,
    CystHistoryItemFactory,
    HormoneReplacementTherapyFactory,
    ImplantedMedicalDeviceHistoryItemFactory,
    MastectomyOrLumpectomyHistoryItemFactory,
    OtherMedicalInformationFactory,
    OtherProcedureHistoryItemFactory,
    ParticipantReportedMammogramFactory,
    PregnancyAndBreastfeedingFactory,
    SymptomFactory,
)


@pytest.mark.django_db
class TestCheckMedicalInformationPresenter:
    def test_no_data(self):
        appointment = AppointmentFactory.create()
        item = CheckMedicalInformationPresenter(appointment)

        assert item.previous_mammograms == "No additional mammograms added"
        assert not item.symptoms
        assert not item.medical_history

    def test_reported_mammogram(self):
        appointment = AppointmentFactory.create()
        ParticipantReportedMammogramFactory.create(appointment=appointment)

        item = CheckMedicalInformationPresenter(appointment)

        assert item.previous_mammograms == "1 additional mammogram added"
        assert not item.symptoms
        assert not item.medical_history

    def test_reported_mammograms(self):
        appointment = AppointmentFactory.create()
        ParticipantReportedMammogramFactory.create_batch(3, appointment=appointment)

        item = CheckMedicalInformationPresenter(appointment)

        assert item.previous_mammograms == "3 additional mammograms added"
        assert not item.symptoms
        assert not item.medical_history

    @pytest.mark.parametrize(
        "expected,test_data",
        [
            (
                "Breast cancer (2000)",
                {
                    "diagnosis_location": BreastCancerHistoryItem.DiagnosisLocationChoices.RIGHT_BREAST,
                    "diagnosis_year": 2000,
                    "right_breast_procedure": BreastCancerHistoryItem.Procedure.LUMPECTOMY,
                    "intervention_location": BreastCancerHistoryItem.InterventionLocation.NHS_HOSPITAL,
                    "intervention_location_details": "East Tester Hospital",
                    "additional_details": "some details",
                },
            ),
            (
                "Breast cancer (year unknown)",
                {
                    "diagnosis_location": BreastCancerHistoryItem.DiagnosisLocationChoices.RIGHT_BREAST,
                    "right_breast_procedure": BreastCancerHistoryItem.Procedure.LUMPECTOMY,
                    "intervention_location": BreastCancerHistoryItem.InterventionLocation.NHS_HOSPITAL,
                    "intervention_location_details": "East Tester Hospital",
                    "additional_details": "some details",
                },
            ),
        ],
    )
    def test_breast_cancer(self, expected, test_data):
        appointment = AppointmentFactory.create()
        BreastCancerHistoryItemFactory.create(
            appointment=appointment,
            **test_data,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.medical_history == [expected]

    @pytest.mark.parametrize(
        "expected,test_data",
        [
            (
                "Implanted cardiac device",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Implanted cardiac device (2020)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                    "procedure_year": 2020,
                },
            ),
            (
                "Implanted cardiac device (removed)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                    "device_has_been_removed": True,
                },
            ),
            (
                "Implanted cardiac device (2020, removed)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                    "procedure_year": 2020,
                    "device_has_been_removed": True,
                },
            ),
            (
                "Implanted cardiac device (removed 2022)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                    "device_has_been_removed": True,
                    "removal_year": 2022,
                },
            ),
            (
                "Implanted cardiac device (2020, removed 2022)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
                    "procedure_year": 2020,
                    "device_has_been_removed": True,
                    "removal_year": 2022,
                },
            ),
            (
                "Implanted Hickman line",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Implanted Hickman line (2020)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "procedure_year": 2020,
                },
            ),
            (
                "Implanted Hickman line (removed)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "device_has_been_removed": True,
                },
            ),
            (
                "Implanted Hickman line (2020, removed)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "procedure_year": 2020,
                    "device_has_been_removed": True,
                },
            ),
            (
                "Implanted Hickman line (removed 2022)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "device_has_been_removed": True,
                    "removal_year": 2022,
                },
            ),
            (
                "Implanted Hickman line (2020, removed 2022)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
                    "procedure_year": 2020,
                    "device_has_been_removed": True,
                    "removal_year": 2022,
                },
            ),
            (
                "Implanted other medical device",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                    "other_medical_device_details": "Test Device",
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Implanted other medical device (2020)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                    "other_medical_device_details": "Test Device",
                    "procedure_year": 2020,
                },
            ),
            (
                "Implanted other medical device (removed)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                    "device_has_been_removed": True,
                },
            ),
            (
                "Implanted other medical device (2020, removed)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                    "procedure_year": 2020,
                    "device_has_been_removed": True,
                },
            ),
            (
                "Implanted other medical device (removed 2022)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                    "other_medical_device_details": "Test Device",
                    "device_has_been_removed": True,
                    "removal_year": 2022,
                },
            ),
            (
                "Implanted other medical device (2020, removed 2022)",
                {
                    "device": ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                    "other_medical_device_details": "Test Device",
                    "procedure_year": 2020,
                    "device_has_been_removed": True,
                    "removal_year": 2022,
                },
            ),
        ],
    )
    def test_implanted_medical_device(self, expected, test_data):
        appointment = AppointmentFactory.create()
        ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=appointment,
            **test_data,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.medical_history == [expected]

    @pytest.mark.parametrize(
        "expected,test_data",
        [
            (
                "Breast implants",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                    ],
                    "additional_details": "some details",
                },
            ),
            (
                "Breast implants (2000)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                    ],
                    "procedure_year": 2000,
                },
            ),
            (
                "Breast implants (removed)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                    ],
                    "implants_have_been_removed": True,
                },
            ),
            (
                "Breast augmentation (2000, removed)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                    ],
                    "procedure_year": 2000,
                    "implants_have_been_removed": True,
                },
            ),
            (
                "Breast augmentation (removed 2020)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "implants_have_been_removed": True,
                    "removal_year": 2020,
                },
            ),
            (
                "Breast augmentation (2000, removed 2020)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "procedure_year": 2000,
                    "implants_have_been_removed": True,
                    "removal_year": 2020,
                },
            ),
            (
                "Breast implants and augmentation",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                    ],
                    "additional_details": "some details",
                },
            ),
            (
                "Breast implants and augmentation (2000)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "procedure_year": 2000,
                },
            ),
            (
                "Breast implants and augmentation (removed)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "implants_have_been_removed": True,
                },
            ),
            (
                "Breast implants and augmentation (2000, removed)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                        BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                    ],
                    "procedure_year": 2000,
                    "implants_have_been_removed": True,
                },
            ),
            (
                "No procedures (2000, removed 2020)",
                {
                    "right_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                    ],
                    "left_breast_procedures": [
                        BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                    ],
                    "procedure_year": 2000,
                    "implants_have_been_removed": True,
                    "removal_year": 2020,
                },
            ),
        ],
    )
    def test_breast_augmentation(self, expected, test_data):
        appointment = AppointmentFactory.create()
        BreastAugmentationHistoryItemFactory.create(
            appointment=appointment, **test_data
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.medical_history == [expected]

    @pytest.mark.parametrize(
        "expected,test_data",
        [
            (
                "Mastectomy (2000)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "year_of_surgery": 2000,
                },
            ),
            (
                "Mastectomy (2001)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "year_of_surgery": 2001,
                },
            ),
            (
                "Mastectomy (2002)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "year_of_surgery": 2002,
                },
            ),
            (
                "Mastectomy (2003)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                    "year_of_surgery": 2003,
                },
            ),
            (
                "Mastectomy (2004)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                    "year_of_surgery": 2004,
                },
            ),
            (
                "Mastectomy (2005)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "year_of_surgery": 2005,
                },
            ),
            (
                "Mastectomy (2006)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "year_of_surgery": 2006,
                },
            ),
            (
                "Mastectomy (2007)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                    "year_of_surgery": 2007,
                },
            ),
            (
                "Lumpectomy (2008)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "year_of_surgery": 2008,
                },
            ),
            (
                "Lumpectomy (2009)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "year_of_surgery": 2009,
                },
            ),
            (
                "Lumpectomy (2010)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                    "year_of_surgery": 2010,
                },
            ),
            (
                "Mastectomy and lumpectomy (2011)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "year_of_surgery": 2011,
                },
            ),
            (
                "Mastectomy and lumpectomy (2012)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                    "year_of_surgery": 2012,
                },
            ),
            (
                "Mastectomy and lumpectomy (2013)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                    "year_of_surgery": 2013,
                },
            ),
            (
                "Mastectomy and lumpectomy (2014)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                    "year_of_surgery": 2014,
                },
            ),
            (
                "No procedure (2014)",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "year_of_surgery": 2014,
                },
            ),
            (
                "Mastectomy",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                },
            ),
            (
                "Lumpectomy",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                },
            ),
            (
                "Mastectomy and lumpectomy",
                {
                    "right_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
                    "left_breast_procedure": MastectomyOrLumpectomyHistoryItem.Procedure.LUMPECTOMY,
                },
            ),
        ],
    )
    def test_format_mastectomy_or_lumpectomy(self, expected, test_data):
        appointment = AppointmentFactory.create()
        MastectomyOrLumpectomyHistoryItemFactory.create(
            appointment=appointment,
            right_breast_other_surgery=[
                MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
            ],
            left_breast_other_surgery=[
                MastectomyOrLumpectomyHistoryItem.Surgery.NO_OTHER_SURGERY
            ],
            surgery_reason=MastectomyOrLumpectomyHistoryItem.SurgeryReason.RISK_REDUCTION,
            additional_details="Some additional details",
            **test_data,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.medical_history == [expected]

    def test_cyst(self):
        appointment = AppointmentFactory.create()
        CystHistoryItemFactory.create(
            appointment=appointment,
            treatment=CystHistoryItem.Treatment.NO_TREATMENT,
            additional_details="Some additional details",
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.medical_history == ["History of cysts"]

    @pytest.mark.parametrize(
        "expected,test_data",
        [
            (
                "Benign lumps (2015)",
                {
                    "right_breast_procedures": [
                        BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY,
                        BenignLumpHistoryItem.Procedure.LUMP_REMOVED,
                    ],
                    "left_breast_procedures": [
                        BenignLumpHistoryItem.Procedure.NO_PROCEDURES
                    ],
                    "procedure_year": 2015,
                    "procedure_location": BenignLumpHistoryItem.ProcedureLocation.PRIVATE_CLINIC_UK,
                    "procedure_location_details": "Harley Street Clinic",
                    "additional_details": "First line\nSecond line",
                },
            ),
            (
                "Benign lumps (year unknown)",
                {
                    "right_breast_procedures": [
                        BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY,
                    ],
                    "left_breast_procedures": [
                        BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY
                    ],
                    "procedure_location": BenignLumpHistoryItem.ProcedureLocation.NHS_HOSPITAL,
                    "procedure_location_details": "Harley Street Clinic",
                    "additional_details": "First line\nSecond line",
                },
            ),
        ],
    )
    def test_benign_lump(self, expected, test_data):
        appointment = AppointmentFactory.create()
        BenignLumpHistoryItemFactory.create(
            appointment=appointment,
            **test_data,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.medical_history == [expected]

    @pytest.mark.parametrize(
        "expected,test_data",
        [
            (
                "Other procedures (breast reduction, 2020)",
                {
                    "procedure": OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
                    "procedure_details": "Lorem ipsum dolor sit amet",
                    "procedure_year": 2020,
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Other procedures (breast reduction)",
                {
                    "procedure": OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
                    "procedure_details": "Lorem ipsum dolor sit amet",
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Other procedures (breast symmetrisation, 2021)",
                {
                    "procedure": OtherProcedureHistoryItem.Procedure.BREAST_SYMMETRISATION,
                    "procedure_details": "Lorem ipsum dolor sit amet",
                    "procedure_year": 2021,
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Other procedures (breast symmetrisation)",
                {
                    "procedure": OtherProcedureHistoryItem.Procedure.BREAST_SYMMETRISATION,
                    "procedure_details": "Lorem ipsum dolor sit amet",
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Other procedures (nipple correction, 2022)",
                {
                    "procedure": OtherProcedureHistoryItem.Procedure.NIPPLE_CORRECTION,
                    "procedure_details": "Lorem ipsum dolor sit amet",
                    "procedure_year": 2022,
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Other procedures (nipple correction)",
                {
                    "procedure": OtherProcedureHistoryItem.Procedure.NIPPLE_CORRECTION,
                    "procedure_details": "Lorem ipsum dolor sit amet",
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Other procedures (Lorem ipsum XYZ 123 _ sit amet, 2023)",
                {
                    "procedure": OtherProcedureHistoryItem.Procedure.OTHER,
                    "procedure_details": "Lorem ipsum XYZ 123 _ sit amet",
                    "procedure_year": 2023,
                    "additional_details": "Some additional details",
                },
            ),
            (
                "Other procedures (XYZ $1_000 sit amet)",
                {
                    "procedure": OtherProcedureHistoryItem.Procedure.OTHER,
                    "procedure_details": "XYZ $1_000 sit amet",
                    "additional_details": "Some additional details",
                },
            ),
        ],
    )
    def test_other_procedure(self, expected, test_data):
        appointment = AppointmentFactory.create()
        OtherProcedureHistoryItemFactory.create(
            appointment=appointment,
            **test_data,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.medical_history == [expected]

    def test_many_medical_history(self):
        appointment = AppointmentFactory.create()
        ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=appointment,
            device=ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
            procedure_year=2018,
        )
        ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=appointment,
            device=ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
        )
        CystHistoryItemFactory.create(
            appointment=appointment,
            treatment=CystHistoryItem.Treatment.NO_TREATMENT,
        )
        OtherProcedureHistoryItemFactory.create(
            appointment=appointment,
            procedure=OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
            procedure_year=2020,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.medical_history == [
            "Implanted Hickman line (2018)",
            "Implanted cardiac device",
            "History of cysts",
            "Other procedures (breast reduction, 2020)",
        ]

    @pytest.mark.parametrize(
        "expected,test_data",
        [
            (
                "Lump (right breast)",
                {
                    "symptom_type_id": SymptomType.LUMP,
                    "area": SymptomAreas.RIGHT_BREAST,
                    "when_started": RelativeDateChoices.SINCE_A_SPECIFIC_DATE,
                    "year_started": 2020,
                    "month_started": 5,
                    "investigated": True,
                    "intermittent": True,
                    "recently_resolved": True,
                    "when_resolved": "3 days ago",
                    "additional_information": "additional information",
                },
            ),
            (
                "Swelling or shape change (left breast)",
                {
                    "symptom_type_id": SymptomType.SWELLING_OR_SHAPE_CHANGE,
                    "area": SymptomAreas.LEFT_BREAST,
                    "when_started": RelativeDateChoices.THREE_MONTHS_TO_A_YEAR,
                },
            ),
            (
                "Skin change: dimples or indentation (right breast)",
                {
                    "symptom_type_id": SymptomType.SKIN_CHANGE,
                    "symptom_sub_type_id": SkinChangeChoices.DIMPLES_OR_INDENTATION,
                    "area": SymptomAreas.RIGHT_BREAST,
                    "when_started": RelativeDateChoices.ONE_TO_THREE_YEARS,
                },
            ),
            (
                "Skin change: rash (left breast)",
                {
                    "symptom_type_id": SymptomType.SKIN_CHANGE,
                    "symptom_sub_type_id": SkinChangeChoices.RASH,
                    "area": SymptomAreas.LEFT_BREAST,
                    "when_started": RelativeDateChoices.ONE_TO_THREE_YEARS,
                },
            ),
            (
                "Skin change: user provided details (both breasts)",
                {
                    "symptom_type_id": SymptomType.SKIN_CHANGE,
                    "symptom_sub_type_id": SkinChangeChoices.OTHER,
                    "symptom_sub_type_details": "user provided details",
                    "area": SymptomAreas.BOTH_BREASTS,
                    "when_started": RelativeDateChoices.OVER_THREE_YEARS,
                },
            ),
            (
                "Nipple change: bloody discharge (left nipple)",
                {
                    "symptom_type_id": SymptomType.NIPPLE_CHANGE,
                    "symptom_sub_type_id": NippleChangeChoices.BLOODY_DISCHARGE,
                    "area": SymptomAreas.LEFT_BREAST,
                    "when_started": RelativeDateChoices.NOT_SURE,
                },
            ),
            (
                "Nipple change: rash or eczema (right nipple)",
                {
                    "symptom_type_id": SymptomType.NIPPLE_CHANGE,
                    "symptom_sub_type_id": NippleChangeChoices.RASH_OR_ECZEMA,
                    "area": SymptomAreas.RIGHT_BREAST,
                    "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS,
                },
            ),
            (
                "Nipple change: user provided details (both nipples)",
                {
                    "symptom_type_id": SymptomType.NIPPLE_CHANGE,
                    "symptom_sub_type_id": NippleChangeChoices.OTHER,
                    "symptom_sub_type_details": "user provided details",
                    "area": SymptomAreas.BOTH_BREASTS,
                    "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS,
                },
            ),
            (
                "user provided details (both breasts)",
                {
                    "symptom_type_id": SymptomType.OTHER,
                    "symptom_sub_type_details": "user provided details",
                    "area": SymptomAreas.BOTH_BREASTS,
                    "when_started": RelativeDateChoices.LESS_THAN_THREE_MONTHS,
                },
            ),
        ],
    )
    def test_sympton(self, expected, test_data):
        appointment = AppointmentFactory.create()
        SymptomFactory.create(
            appointment=appointment,
            area_description="area description",
            **test_data,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.symptoms == [expected]

    def test_many_symptons(self):
        appointment = AppointmentFactory.create()
        SymptomFactory.create(
            appointment=appointment,
            symptom_type_id=SymptomType.SKIN_CHANGE,
            symptom_sub_type_id=SkinChangeChoices.COLOUR_CHANGE,
            area=SymptomAreas.LEFT_BREAST,
            when_started=RelativeDateChoices.ONE_TO_THREE_YEARS,
            area_description="area description",
        )
        SymptomFactory.create(
            appointment=appointment,
            symptom_type_id=SymptomType.LUMP,
            area=SymptomAreas.RIGHT_BREAST,
            when_started=RelativeDateChoices.OVER_THREE_YEARS,
            area_description="area description",
        )
        SymptomFactory.create(
            appointment=appointment,
            symptom_type_id=SymptomType.SWELLING_OR_SHAPE_CHANGE,
            area=SymptomAreas.RIGHT_BREAST,
            when_started=RelativeDateChoices.NOT_SURE,
            area_description="area description",
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert len(item.symptoms) == 3
        assert "Skin change: colour change (left breast)" in item.symptoms
        assert "Lump (right breast)" in item.symptoms
        assert "Swelling or shape change (right breast)" in item.symptoms

    def test_no_other_relevant_information(self):
        appointment = AppointmentFactory.create()

        item = CheckMedicalInformationPresenter(appointment)

        assert not item.other_relevant_information

    def test_hormone_replacement_therapy_yes(self):
        appointment = AppointmentFactory.create()
        HormoneReplacementTherapyFactory.create(
            appointment=appointment,
            status=HormoneReplacementTherapy.Status.YES,
            approx_start_date="Summer 2022",
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.other_relevant_information == ["Taking HRT (Summer 2022)"]

    def test_hormone_replacement_therapy_no_but_stopped_recently(self):
        appointment = AppointmentFactory.create()
        HormoneReplacementTherapyFactory.create(
            appointment=appointment,
            status=HormoneReplacementTherapy.Status.NO_BUT_STOPPED_RECENTLY,
            approx_previous_duration="2 years",
            approx_end_date="Winter 2023",
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.other_relevant_information == ["Recently stopped HRT (Winter 2023)"]

    def test_hormone_replacement_therapy_no(self):
        appointment = AppointmentFactory.create()
        HormoneReplacementTherapyFactory.create(
            appointment=appointment,
            status=HormoneReplacementTherapy.Status.NO,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert not item.other_relevant_information

    def test_pregnancy_yes(self):
        appointment = AppointmentFactory.create()
        PregnancyAndBreastfeedingFactory.create(
            appointment=appointment,
            pregnancy_status=PregnancyAndBreastfeeding.PregnancyStatus.YES,
            approx_pregnancy_due_date="November 2022",
            breastfeeding_status=PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.other_relevant_information == ["Pregnant (November 2022)"]

    def test_pregnancy_no_but_has_been_recently(self):
        appointment = AppointmentFactory.create()
        PregnancyAndBreastfeedingFactory.create(
            appointment=appointment,
            pregnancy_status=PregnancyAndBreastfeeding.PregnancyStatus.NO_BUT_HAS_BEEN_RECENTLY,
            approx_pregnancy_end_date="December 2023",
            breastfeeding_status=PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.other_relevant_information == ["Recently pregnant (December 2023)"]

    def test_breast_feeding_yes(self):
        appointment = AppointmentFactory.create()
        PregnancyAndBreastfeedingFactory.create(
            appointment=appointment,
            pregnancy_status=PregnancyAndBreastfeeding.PregnancyStatus.NO,
            breastfeeding_status=PregnancyAndBreastfeeding.BreastfeedingStatus.YES,
            approx_breastfeeding_start_date="November 2022",
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.other_relevant_information == ["Breastfeeding (November 2022)"]

    def test_breastfeeding_no_but_stopped_recently(self):
        appointment = AppointmentFactory.create()
        PregnancyAndBreastfeedingFactory.create(
            appointment=appointment,
            pregnancy_status=PregnancyAndBreastfeeding.PregnancyStatus.NO,
            breastfeeding_status=PregnancyAndBreastfeeding.BreastfeedingStatus.NO_BUT_STOPPED_RECENTLY,
            approx_breastfeeding_end_date="December 2023",
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.other_relevant_information == [
            "Recently stopped breastfeeding (December 2023)"
        ]

    def test_other_medical_information(self):
        appointment = AppointmentFactory.create()
        OtherMedicalInformationFactory.create(
            appointment=appointment,
            details="Some other medical information",
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.other_relevant_information == ["Some other medical information"]

    def test_full_other_medical_information(self):
        appointment = AppointmentFactory.create()
        HormoneReplacementTherapyFactory.create(
            appointment=appointment,
            status=HormoneReplacementTherapy.Status.YES,
            approx_start_date="Summer 2022",
        )
        PregnancyAndBreastfeedingFactory.create(
            appointment=appointment,
            pregnancy_status=PregnancyAndBreastfeeding.PregnancyStatus.YES,
            approx_pregnancy_due_date="November 2022",
            breastfeeding_status=PregnancyAndBreastfeeding.BreastfeedingStatus.NO_BUT_STOPPED_RECENTLY,
            approx_breastfeeding_end_date="December 2023",
        )
        OtherMedicalInformationFactory.create(
            appointment=appointment,
            details="Some other medical information",
        )

        item = CheckMedicalInformationPresenter(appointment)

        assert item.other_relevant_information == [
            "Taking HRT (Summer 2022)",
            "Pregnant (November 2022)",
            "Recently stopped breastfeeding (December 2023)",
            "Some other medical information",
        ]
