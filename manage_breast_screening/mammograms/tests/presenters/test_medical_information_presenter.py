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

    def test_implanted_medical_device_history_link(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(
            appointment
        ).add_implanted_medical_device_history_link == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/implanted-medical-device-history/",
            "text": "Add implanted medical device history",
        }

    def test_cyst_history_link(self):
        appointment = AppointmentFactory()

        assert MedicalInformationPresenter(appointment).add_cyst_history_link == {
            "href": f"/mammograms/{appointment.pk}/record-medical-information/cyst-history/",
            "text": "Add cyst history",
        }
