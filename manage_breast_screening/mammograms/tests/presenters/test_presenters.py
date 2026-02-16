from uuid import uuid4

import pytest

from manage_breast_screening.mammograms.presenters import present_secondary_nav


class TestSecondaryNav:
    @pytest.fixture(autouse=True)
    def pk(self):
        return uuid4()

    def test_active_appointment(self, pk):
        assert present_secondary_nav(pk, current_tab="appointment") == [
            {
                "current": True,
                "href": f"/mammograms/{pk}/",
                "id": "appointment",
                "text": "Appointment",
            },
            {
                "current": False,
                "href": f"/mammograms/{pk}/participant/",
                "id": "participant",
                "text": "Participant",
            },
            {
                "current": False,
                "href": f"/mammograms/{pk}/medical-information/",
                "id": "medical_information",
                "text": "Medical information",
            },
            {
                "current": False,
                "href": f"/mammograms/{pk}/note/",
                "id": "note",
                "text": "Note",
            },
        ]

    def test_complete_appointment(self, pk):
        assert present_secondary_nav(
            pk, current_tab="appointment", appointment_complete=True
        ) == [
            {
                "current": True,
                "href": f"/mammograms/{pk}/",
                "id": "appointment",
                "text": "Appointment",
            },
            {
                "current": False,
                "href": f"/mammograms/{pk}/participant/",
                "id": "participant",
                "text": "Participant",
            },
            {
                "current": False,
                "href": f"/mammograms/{pk}/medical-information/",
                "id": "medical_information",
                "text": "Medical information",
            },
            {
                "current": False,
                "href": f"/mammograms/{pk}/images/",
                "id": "images",
                "text": "Images",
            },
            {
                "current": False,
                "href": f"/mammograms/{pk}/note/",
                "id": "note",
                "text": "Note",
            },
        ]

    @pytest.mark.parametrize(
        "current_tab",
        ["appointment", "participant", "medical_information", "images", "note"],
    )
    def test_current_tab(self, pk, current_tab):
        tabs = present_secondary_nav(
            pk, current_tab=current_tab, appointment_complete=True
        )
        current = [tab for tab in tabs if tab["current"]]

        assert len(current) == 1
        assert current[0]["id"] == current_tab
