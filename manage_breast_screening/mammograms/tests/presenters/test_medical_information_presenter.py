import pytest

from manage_breast_screening.mammograms.presenters.medical_information_presenter import (
    MedicalInformationPresenter,
)
from manage_breast_screening.participants.models import MedicalInformationSection
from manage_breast_screening.participants.models.breast_features import (
    BreastFeatureAnnotation,
)
from manage_breast_screening.participants.models.other_information.hormone_replacement_therapy import (
    HormoneReplacementTherapy,
)
from manage_breast_screening.participants.models.other_information.pregnancy_and_breastfeeding import (
    PregnancyAndBreastfeeding,
)
from manage_breast_screening.participants.models.symptom import (
    RelativeDateChoices,
    SymptomAreas,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BreastAugmentationHistoryItemFactory,
    CystHistoryItemFactory,
    ImplantedMedicalDeviceHistoryItemFactory,
    MastectomyOrLumpectomyHistoryItemFactory,
    MedicalInformationReviewFactory,
    OtherProcedureHistoryItemFactory,
    SymptomFactory,
)


@pytest.mark.django_db
class TestRecordMedicalInformationPresenter:
    def test_formats_symptoms_summary_list(self):
        appointment = AppointmentFactory.create()

        symptom1 = SymptomFactory.create(
            lump=True,
            appointment=appointment,
            when_started=RelativeDateChoices.NOT_SURE,
            area=SymptomAreas.LEFT_BREAST,
            intermittent=True,
            when_resolved="resolved date",
            additional_information="abc",
        )

        symptom2 = SymptomFactory.create(
            swelling_or_shape_change=True,
            appointment=appointment,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
            area=SymptomAreas.BOTH_BREASTS,
        )

        presenter = MedicalInformationPresenter(appointment)

        assert presenter.symptom_rows == [
            {
                "actions": {
                    "items": [
                        {
                            "href": f"/mammograms/{appointment.id}/record-medical-information/lump/{symptom1.id}/",
                            "classes": "nhsuk-link--no-visited-state",
                            "text": "Change",
                            "visuallyHiddenText": "lump",
                        },
                    ],
                },
                "key": {
                    "text": "Lump",
                },
                "value": {
                    "html": "Left breast<br>Not sure<br>Not investigated<br>Symptom is intermittent<br>Stopped: resolved date<br>Additional information: abc",
                },
            },
            {
                "actions": {
                    "items": [
                        {
                            "href": f"/mammograms/{appointment.id}/record-medical-information/swelling-or-shape-change/{symptom2.id}/",
                            "classes": "nhsuk-link--no-visited-state",
                            "text": "Change",
                            "visuallyHiddenText": "swelling or shape change",
                        },
                    ],
                },
                "key": {
                    "text": "Swelling or shape change",
                },
                "value": {
                    "html": "Both breasts<br>Less than 3 months ago<br>Not investigated",
                },
            },
        ]

    def test_add_lump_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(appointment).add_lump_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/lump/",
            "text": "Lump",
        }

    def test_add_nipple_change_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(appointment).add_nipple_change_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/nipple-change/",
            "text": "Nipple change",
        }

    def test_add_breast_cancer_history_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(
            appointment
        ).add_breast_cancer_history_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/breast-cancer-history/",
            "text": "Breast cancer",
        }

    def test_implanted_medical_device_history_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(
            appointment
        ).add_implanted_medical_device_history_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/implanted-medical-device-history/",
            "text": "Implanted medical device",
        }

    def test_implanted_medical_device_history_items_have_a_counter(self):
        appointment = AppointmentFactory()
        ImplantedMedicalDeviceHistoryItemFactory.create_batch(
            2, appointment=appointment
        )

        counters = [
            item.counter
            for item in MedicalInformationPresenter(
                appointment
            ).implanted_medical_device_history
        ]

        assert counters == [1, 2]

    def test_single_implanted_medical_device_history_item_has_no_counter(self):
        appointment = AppointmentFactory()
        ImplantedMedicalDeviceHistoryItemFactory.create(appointment=appointment)

        counters = [
            item.counter
            for item in MedicalInformationPresenter(
                appointment
            ).implanted_medical_device_history
        ]

        assert counters == [None]

    def test_cyst_history_items_have_a_counter(self):
        appointment = AppointmentFactory()
        CystHistoryItemFactory.create_batch(2, appointment=appointment)

        counters = [
            item.counter
            for item in MedicalInformationPresenter(appointment).cyst_history
        ]

        assert counters == [1, 2]

    def test_single_cyst_history_item_has_no_counter(self):
        appointment = AppointmentFactory()
        CystHistoryItemFactory.create(appointment=appointment)

        counters = [
            item.counter
            for item in MedicalInformationPresenter(appointment).cyst_history
        ]

        assert counters == [None]

    def test_cyst_history_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(appointment).add_cyst_history_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/cyst-history/",
            "text": "Cysts",
        }

    def test_certain_items_can_only_be_added_once(self):
        appointment = AppointmentFactory()
        CystHistoryItemFactory.create(appointment=appointment)
        BreastAugmentationHistoryItemFactory.create(appointment=appointment)

        assert MedicalInformationPresenter(appointment).add_cyst_history_button is None
        assert (
            MedicalInformationPresenter(
                appointment
            ).add_breast_augmentation_history_button
            is None
        )

    def test_breast_augmentation_history_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(
            appointment
        ).add_breast_augmentation_history_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/breast-augmentation-history/",
            "text": "Breast implants or augmentation",
        }

    def test_add_benign_lump_history_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(
            appointment
        ).add_benign_lump_history_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/benign-lump-history/",
            "text": "Benign lumps",
        }

    def test_mastectomy_or_lumpectomy_history_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(
            appointment
        ).add_mastectomy_or_lumpectomy_history_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/mastectomy-or-lumpectomy-history/",
            "text": "Mastectomy or lumpectomy",
        }

    def test_mastectomy_or_lumpectomy_history_items_have_a_counter(self):
        appointment = AppointmentFactory()
        MastectomyOrLumpectomyHistoryItemFactory.create_batch(
            2, appointment=appointment
        )

        counters = [
            item.counter
            for item in MedicalInformationPresenter(
                appointment
            ).mastectomy_or_lumpectomy_history
        ]

        assert counters == [1, 2]

    def test_single_mastectomy_or_lumpectomy_history_item_has_no_counter(self):
        appointment = AppointmentFactory()
        MastectomyOrLumpectomyHistoryItemFactory.create(appointment=appointment)

        counters = [
            item.counter
            for item in MedicalInformationPresenter(
                appointment
            ).mastectomy_or_lumpectomy_history
        ]

        assert counters == [None]

    def test_other_procedure_history_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(
            appointment
        ).add_other_procedure_history_button == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/other-procedure-history/",
            "text": "Other procedures",
        }

    def test_other_procedure_history_items_have_a_counter(self):
        appointment = AppointmentFactory()
        OtherProcedureHistoryItemFactory.create_batch(2, appointment=appointment)

        counters = [
            item.counter
            for item in MedicalInformationPresenter(appointment).other_procedure_history
        ]

        assert counters == [1, 2]

    def test_single_other_procedure_history_item_has_no_counter(self):
        appointment = AppointmentFactory()
        OtherProcedureHistoryItemFactory.create(appointment=appointment)

        counters = [
            item.counter
            for item in MedicalInformationPresenter(appointment).other_procedure_history
        ]

        assert counters == [None]

    def test_add_mammogram_button(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(appointment).add_mammogram_button == {
            "href": (
                f"/mammograms/{appointment.pk}/previous-mammograms/add"
                + f"?return_url=/mammograms/{appointment.pk}/record-medical-information/"
            ),
            "text": "Add another mammogram",
        }

    def test_any_medical_history(self):
        appointment = AppointmentFactory()
        assert not MedicalInformationPresenter(appointment).any_medical_history

        OtherProcedureHistoryItemFactory.create(appointment=appointment)
        assert MedicalInformationPresenter(appointment).any_medical_history

    def test_add_hormone_replacement_therapy_link(self):
        appointment = AppointmentFactory()

        presenter = MedicalInformationPresenter(appointment)

        assert presenter.hormone_replacement_therapy is None
        assert presenter.add_hormone_replacement_therapy_link == (
            f"/mammograms/{appointment.pk}/record-medical-information/hormone-replacement-therapy/"
        )

    def test_hormone_replacement_therapy_actions_present(self):
        appointment = AppointmentFactory()
        hormone_replacement_therapy = HormoneReplacementTherapy.objects.create(
            appointment=appointment, status=HormoneReplacementTherapy.Status.YES
        )

        presenter = MedicalInformationPresenter(appointment)

        assert presenter.hormone_replacement_therapy == hormone_replacement_therapy
        assert presenter.hormone_replacement_therapy_actions(read_only=False) == {
            "items": [
                {
                    "classes": "nhsuk-link--no-visited-state",
                    "href": f"/mammograms/{appointment.pk}/record-medical-information/hormone-replacement-therapy/{hormone_replacement_therapy.pk}/",
                    "text": "Change",
                    "visuallyHiddenText": "hormone replacement therapy",
                }
            ]
        }

    def test_hormone_replacement_therapy_actions_readonly(self):
        appointment = AppointmentFactory()
        hormone_replacement_therapy = HormoneReplacementTherapy.objects.create(
            appointment=appointment, status=HormoneReplacementTherapy.Status.YES
        )

        presenter = MedicalInformationPresenter(appointment)

        assert presenter.hormone_replacement_therapy == hormone_replacement_therapy
        assert not presenter.hormone_replacement_therapy_actions(read_only=True)

    def test_hormone_replacement_therapy_actions_none(self):
        appointment = AppointmentFactory()

        presenter = MedicalInformationPresenter(appointment)

        assert not presenter.hormone_replacement_therapy_actions()

    def test_add_pregnancy_and_breastfeeding_link(self):
        appointment = AppointmentFactory()

        presenter = MedicalInformationPresenter(appointment)

        assert presenter.pregnancy_and_breastfeeding is None
        assert presenter.add_pregnancy_and_breastfeeding_link == (
            f"/mammograms/{appointment.pk}/record-medical-information/pregnancy-and-breastfeeding/"
        )

    def test_pregnancy_and_breastfeeding_actions_present(self):
        appointment = AppointmentFactory()
        pregnancy_and_breastfeeding = PregnancyAndBreastfeeding.objects.create(
            appointment=appointment,
            pregnancy_status=PregnancyAndBreastfeeding.PregnancyStatus.NO,
            breastfeeding_status=PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
        )

        presenter = MedicalInformationPresenter(appointment)

        assert presenter.pregnancy_and_breastfeeding == pregnancy_and_breastfeeding
        assert presenter.pregnancy_and_breastfeeding_actions(read_only=False) == {
            "items": [
                {
                    "classes": "nhsuk-link--no-visited-state",
                    "href": f"/mammograms/{appointment.pk}/record-medical-information/pregnancy-and-breastfeeding/{pregnancy_and_breastfeeding.pk}/",
                    "text": "Change",
                    "visuallyHiddenText": "pregnancy and breastfeeding",
                }
            ]
        }

    def test_pregnancy_and_breastfeeding_actions_readonly(self):
        appointment = AppointmentFactory()
        pregnancy_and_breastfeeding = PregnancyAndBreastfeeding.objects.create(
            appointment=appointment,
            pregnancy_status=PregnancyAndBreastfeeding.PregnancyStatus.NO,
            breastfeeding_status=PregnancyAndBreastfeeding.BreastfeedingStatus.NO,
        )

        presenter = MedicalInformationPresenter(appointment)

        assert presenter.pregnancy_and_breastfeeding == pregnancy_and_breastfeeding
        assert not presenter.pregnancy_and_breastfeeding_actions(read_only=True)

    def test_pregnancy_and_breastfeeding_actions_none(self):
        appointment = AppointmentFactory()

        presenter = MedicalInformationPresenter(appointment)

        assert not presenter.pregnancy_and_breastfeeding_actions()

    def test_add_breast_features_button(self, in_progress_appointment):
        presenter = MedicalInformationPresenter(in_progress_appointment)

        assert presenter.add_or_update_breast_features_button == {
            "href": f"/mammograms/{in_progress_appointment.pk}/record-medical-information/breast-features/update/",
            "text": "Add a feature",
        }

    def test_update_breast_features_button(self, in_progress_appointment):
        in_progress_appointment.breast_features = BreastFeatureAnnotation(
            appointment=in_progress_appointment,
            annotations_json=[{"name": "abc", "id": "abc", "x": 1, "y": 1}],
        )

        presenter = MedicalInformationPresenter(in_progress_appointment)

        assert presenter.add_or_update_breast_features_button == {
            "href": f"/mammograms/{in_progress_appointment.pk}/record-medical-information/breast-features/update/",
            "text": "View or edit breast features",
        }


@pytest.mark.django_db
class TestSectionPresenter:
    @pytest.mark.parametrize(
        "section,expected_anchor",
        [
            (MedicalInformationSection.MAMMOGRAM_HISTORY, "mammogram-history"),
            (MedicalInformationSection.SYMPTOMS, "symptoms"),
            (MedicalInformationSection.MEDICAL_HISTORY, "medical-history"),
            (MedicalInformationSection.BREAST_FEATURES, "breast-features"),
            (MedicalInformationSection.OTHER_INFORMATION, "other-information"),
        ],
    )
    def test_anchor(self, in_progress_appointment, section, expected_anchor):
        presenter = MedicalInformationPresenter(in_progress_appointment)

        assert presenter.get_section(section).anchor == expected_anchor

    def test_is_reviewed(self, in_progress_appointment):
        MedicalInformationReviewFactory.create(
            appointment=in_progress_appointment,
            section=MedicalInformationSection.SYMPTOMS,
        )
        presenter = MedicalInformationPresenter(in_progress_appointment)

        assert presenter.get_section(MedicalInformationSection.SYMPTOMS).is_reviewed
        assert not presenter.get_section(
            MedicalInformationSection.BREAST_FEATURES
        ).is_reviewed

    def test_next_anchor(self, in_progress_appointment):
        assert (
            MedicalInformationPresenter(in_progress_appointment)
            .get_section(MedicalInformationSection.MAMMOGRAM_HISTORY)
            .next_anchor
            == "symptoms"
        )

        assert (
            MedicalInformationPresenter(in_progress_appointment)
            .get_section(MedicalInformationSection.OTHER_INFORMATION)
            .next_anchor
            is None
        )

    def test_next_section_link(self, in_progress_appointment):
        assert MedicalInformationPresenter(in_progress_appointment).get_section(
            MedicalInformationSection.MAMMOGRAM_HISTORY
        ).next_section_link == {"href": "#symptoms", "text": "Next section"}

        assert (
            MedicalInformationPresenter(in_progress_appointment)
            .get_section(MedicalInformationSection.OTHER_INFORMATION)
            .next_section_link
            is None
        )

    def test_review_button(self, in_progress_appointment):
        assert MedicalInformationPresenter(in_progress_appointment).get_section(
            MedicalInformationSection.MAMMOGRAM_HISTORY
        ).review_button == {
            "href": f"/mammograms/{in_progress_appointment.pk}/record-medical-information/mark-reviewed/MAMMOGRAM_HISTORY/",
            "text": "Mark as reviewed",
        }

        assert MedicalInformationPresenter(in_progress_appointment).get_section(
            MedicalInformationSection.OTHER_INFORMATION
        ).review_button == {
            "href": f"/mammograms/{in_progress_appointment.pk}/record-medical-information/mark-reviewed/OTHER_INFORMATION/",
            "text": "Mark as reviewed",
        }
