from unittest.mock import MagicMock

import pytest

from manage_breast_screening.mammograms.presenters import present_secondary_nav
from manage_breast_screening.participants.models.appointment import Appointment


class TestSecondaryNav:
    @pytest.fixture
    def mock_appointment_with_images(self):
        mock_appointment = MagicMock(spec=Appointment)
        mock_appointment.pk = "53ce8d3b-9e65-471a-b906-73809c0475d0"
        mock_appointment.has_study.return_value = True
        return mock_appointment

    @pytest.fixture
    def mock_appointment_without_images(self):
        mock_appointment = MagicMock(spec=Appointment)
        mock_appointment.pk = "53ce8d3b-9e65-471a-b906-73809c0475d0"
        mock_appointment.has_study.return_value = False
        return mock_appointment

    def test_active_appointment(self, mock_appointment_without_images):
        pk = mock_appointment_without_images.pk
        mock_appointment_without_images.has_study.return_value = False
        assert present_secondary_nav(
            mock_appointment_without_images, current_tab="appointment"
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
                "href": f"/mammograms/{pk}/note/",
                "id": "note",
                "text": "Note",
            },
        ]

    def test_complete_appointment(self, mock_appointment_with_images):
        pk = mock_appointment_with_images.pk
        assert present_secondary_nav(
            mock_appointment_with_images, current_tab="appointment"
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
    def test_current_tab(self, mock_appointment_with_images, current_tab):
        tabs = present_secondary_nav(
            mock_appointment_with_images, current_tab=current_tab
        )
        current = [tab for tab in tabs if tab["current"]]

        assert len(current) == 1
        assert current[0]["id"] == current_tab
