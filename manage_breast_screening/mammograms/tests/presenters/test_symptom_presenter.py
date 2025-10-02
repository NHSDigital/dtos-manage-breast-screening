from datetime import date

import pytest

from manage_breast_screening.mammograms.presenters.symptom_presenter import (
    SymptomPresenter,
)
from manage_breast_screening.participants.models.symptom import (
    RelativeDateChoices,
    SymptomAreas,
)
from manage_breast_screening.participants.tests.factories import SymptomFactory


@pytest.mark.django_db
class TestSymptomPresenter:
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

        presenter = SymptomPresenter(lump)

        assert presenter.area_line == expected_location

    def test_present_change_type(self):
        inversion = SymptomFactory.create(
            inversion=True,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
            area=SymptomAreas.BOTH_BREASTS,
            investigated=False,
        )

        assert SymptomPresenter(inversion).change_type_line == "Change type: inversion"

    def test_present_change_type_other(self):
        other_change = SymptomFactory.create(
            other_skin_change=True,
            when_started=RelativeDateChoices.NOT_SURE,
            area=SymptomAreas.OTHER,
            investigated=False,
            symptom_sub_type_details="abc",
        )

        assert SymptomPresenter(other_change).change_type_line == "Change type: abc"

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

        presenter = SymptomPresenter(symptom)

        assert presenter.investigated_line == "Previously investigated: abc"
        assert presenter.started_line == "January 2025 (8 months ago)"

    def test_formats_intermittent_stopped_and_additional_information(self):
        symptom = SymptomFactory.create(
            lump=True,
            when_started=RelativeDateChoices.NOT_SURE,
            area=SymptomAreas.LEFT_BREAST,
            intermittent=True,
            when_resolved="resolved date",
            additional_information="abc",
        )

        presenter = SymptomPresenter(symptom)

        assert presenter.stopped_line == "Stopped: resolved date"
        assert presenter.intermittent_line == "Symptom is intermittent"
        assert presenter.additional_information_line == "Additional information: abc"

    def test_formats_for_summary_list(self):
        symptom = SymptomFactory.create(
            lump=True,
            when_started=RelativeDateChoices.NOT_SURE,
            area=SymptomAreas.LEFT_BREAST,
            intermittent=True,
            when_resolved="resolved date",
            additional_information="abc",
        )

        presenter = SymptomPresenter(symptom)

        assert presenter.summary_list_row == {
            "actions": {
                "items": [
                    {
                        "href": f"/mammograms/{symptom.appointment_id}/record-medical-information/lump/{symptom.id}/",
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
        }
