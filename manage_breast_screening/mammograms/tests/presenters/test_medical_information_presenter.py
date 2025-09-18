import pytest

from manage_breast_screening.mammograms.presenters.medical_information_presenter import (
    MedicalInformationPresenter,
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
    def test_returns_symptoms(self, area, expected_location):
        symptom = SymptomFactory.create(
            lump=True,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
            area=area,
            investigated=False,
        )

        presenter = MedicalInformationPresenter(symptom.appointment)

        assert presenter.symptoms == [
            MedicalInformationPresenter.PresentedSymptom(
                symptom_type="Lump",
                location_line=expected_location,
                started_line="Less than 3 months",
                investigated_line="Not investigated",
            ),
        ]

    def test_formats_investigation_and_specific_date(self):
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
            MedicalInformationPresenter.PresentedSymptom(
                symptom_type="Lump",
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
            MedicalInformationPresenter.PresentedSymptom(
                symptom_type="Lump",
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

        SymptomFactory.create(
            lump=True,
            appointment=appointment,
            when_started=RelativeDateChoices.NOT_SURE,
            area=SymptomAreas.LEFT_BREAST,
            intermittent=True,
            when_resolved="resolved date",
            additional_information="abc",
        )

        SymptomFactory.create(
            skin_change=True,
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
                            "href": "#",
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
                            "href": "#",
                            "text": "Change",
                            "visuallyHiddenText": "skin change",
                        },
                    ],
                },
                "key": {
                    "text": "Skin change",
                },
                "value": {
                    "html": "Both breasts<br>Less than 3 months<br>Not investigated",
                },
            },
        ]
