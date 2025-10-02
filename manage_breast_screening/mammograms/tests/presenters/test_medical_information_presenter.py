from datetime import date

import pytest

from manage_breast_screening.mammograms.presenters.medical_information_presenter import (
    MedicalInformationPresenter,
    PresentedSymptom,
)
from manage_breast_screening.participants.models.symptom import (
    RelativeDateChoices,
    SymptomAreas,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    SymptomFactory,
)


@pytest.mark.django_db
class TestRecordMedicalInformationPresenter:
    @pytest.mark.parametrize(
        "area, expected_location",
        [
            (SymptomAreas.RIGHT_BREAST, "Right breast"),
            (SymptomAreas.LEFT_BREAST, "Left breast"),
            (SymptomAreas.OTHER, "Other"),
        ],
    )
    def test_presents_symptoms_with_area(self, area, expected_location):
        lump = SymptomFactory.create(
            lump=True,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
            area=area,
            investigated=False,
        )

        presenter = MedicalInformationPresenter(lump.appointment)

        assert presenter.symptoms == [
            PresentedSymptom(
                id=lump.id,
                appointment_id=lump.appointment.id,
                symptom_type_id="LUMP",
                symptom_type_name="Lump",
                location_line=expected_location,
                started_line="Less than 3 months ago",
                investigated_line="Not investigated",
            ),
        ]

    def test_formats_area(self):
        symptom = SymptomFactory.create(
            lump=True,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
            area=SymptomAreas.OTHER,
            area_description="abc",
        )

        presenter = MedicalInformationPresenter(symptom.appointment)

        assert presenter.symptoms == [
            PresentedSymptom(
                id=symptom.id,
                appointment_id=symptom.appointment_id,
                symptom_type_id="LUMP",
                symptom_type_name="Lump",
                location_line="Other: abc",
                started_line="Less than 3 months ago",
                investigated_line="Not investigated",
            )
        ]

    def test_presents_symptoms_with_subtypes(self):
        appointment = AppointmentFactory.create()

        inversion = SymptomFactory.create(
            inversion=True,
            appointment=appointment,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
            area=SymptomAreas.BOTH_BREASTS,
            investigated=False,
        )

        other_change = SymptomFactory.create(
            other_skin_change=True,
            appointment=appointment,
            when_started=RelativeDateChoices.NOT_SURE,
            area=SymptomAreas.OTHER,
            investigated=False,
            symptom_sub_type_details="abc",
        )

        presenter = MedicalInformationPresenter(appointment)

        assert presenter.symptoms == [
            PresentedSymptom(
                id=inversion.id,
                appointment_id=appointment.id,
                symptom_type_id="NIPPLE_CHANGE",
                symptom_type_name="Nipple change",
                location_line="Both breasts",
                started_line="Less than 3 months ago",
                change_type_line="Change type: inversion",
                investigated_line="Not investigated",
            ),
            PresentedSymptom(
                id=other_change.id,
                appointment_id=appointment.id,
                symptom_type_id="SKIN_CHANGE",
                symptom_type_name="Skin change",
                location_line="Other",
                started_line="Not sure",
                change_type_line="Change type: abc",
                investigated_line="Not investigated",
            ),
        ]

    def test_formats_investigation_and_specific_date(self, time_machine):
        time_machine.move_to(date(2025, 9, 1))

        symptom = SymptomFactory.create(
            lump=True,
            when_started=RelativeDateChoices.SINCE_A_SPECIFIC_DATE,
            year_started=2025,
            month_started=1,
            area=SymptomAreas.RIGHT_BREAST,
            investigated=True,
            investigation_details="abc",
        )

        presenter = MedicalInformationPresenter(symptom.appointment)

        assert presenter.symptoms == [
            PresentedSymptom(
                id=symptom.id,
                appointment_id=symptom.appointment_id,
                symptom_type_id="LUMP",
                symptom_type_name="Lump",
                location_line="Right breast",
                started_line="January 2025 (8 months ago)",
                investigated_line="Previously investigated: abc",
            ),
        ]

    def test_formats_intermittent_stopped_and_additional_information(self):
        symptom = SymptomFactory.create(
            lump=True,
            when_started=RelativeDateChoices.NOT_SURE,
            area=SymptomAreas.LEFT_BREAST,
            intermittent=True,
            when_resolved="resolved date",
            additional_information="abc",
        )

        presenter = MedicalInformationPresenter(symptom.appointment)

        assert presenter.symptoms == [
            PresentedSymptom(
                id=symptom.id,
                appointment_id=symptom.appointment_id,
                symptom_type_id="LUMP",
                symptom_type_name="Lump",
                location_line="Left breast",
                started_line="Not sure",
                stopped_line="Stopped: resolved date",
                investigated_line="Not investigated",
                intermittent_line="Symptom is intermittent",
                additional_information_line="Additional information: abc",
            ),
        ]

    def test_formats_for_summary_list(self):
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

    def test_add_lump_link(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(appointment).add_lump_link == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/lump/",
            "text": "Add a lump",
        }

        SymptomFactory.create(
            appointment=appointment,
            lump=True,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
            area=SymptomAreas.BOTH_BREASTS,
        )

        assert MedicalInformationPresenter(appointment).add_lump_link == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/lump/",
            "text": "Add another lump",
        }

    def test_add_nipple_change_link(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(appointment).add_nipple_change_link == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/nipple-change/",
            "text": "Add a nipple change",
        }

        SymptomFactory.create(
            appointment=appointment,
            inversion=True,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
            area=SymptomAreas.BOTH_BREASTS,
        )

        assert MedicalInformationPresenter(appointment).add_nipple_change_link == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/nipple-change/",
            "text": "Add another nipple change",
        }
