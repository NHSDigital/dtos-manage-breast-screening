import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from django.urls import reverse

from ..models import Clinic
from ..presenters import AppointmentListPresenter, ClinicPresenter
from .factories import ClinicStatusFactory


@pytest.fixture
def mock_clinic():
    mock = MagicMock(spec=Clinic)

    mock.starts_at = datetime(2025, 1, 1, 9)
    mock.session_type.return_value = "All day"
    mock.clinic_slots.count.return_value = 10
    mock.setting.name = "Test setting"
    mock.time_range.return_value = {
        "start_time": datetime(2025, 1, 1, 9),
        "end_time": datetime(2025, 1, 1, 15),
    }
    mock.get_type_display.return_value = "Screening"
    mock.get_risk_type_display.return_value = "Routine"
    mock.current_status = ClinicStatusFactory.build()

    return mock


def test_clinic_presenter(mock_clinic):
    presenter = ClinicPresenter(mock_clinic)

    assert presenter.starts_at == "1 January 2025"
    assert presenter.session_type == "All day"
    assert presenter.number_of_slots == 10
    assert presenter.location_name == "Test setting"
    assert presenter.time_range == "9am to 3pm"
    assert presenter.type == "Screening"
    assert presenter.risk_type == "Routine"
    assert presenter.state == {
        "classes": "nhsuk-tag--blue",
        "text": "Scheduled",
    }


class TestAppointmentListPresenter:
    @pytest.mark.django_db
    def test_secondary_nav_data(self):
        clinic_pk = uuid.uuid4()
        filter_value = "checked_in"
        counts_by_filter = {
            "remaining": 5,
            "checked_in": 3,
            "in_progress": 2,
            "complete": 2,
            "all": 10,
        }

        presenter = AppointmentListPresenter(
            clinic_pk, [], filter_value, counts_by_filter
        )
        nav_data = presenter.secondary_nav_data

        assert nav_data[0]["label"] == "Remaining"
        assert nav_data[0]["count"] == 5
        expected_remaining_url = reverse(
            "clinics:show_remaining", kwargs={"pk": clinic_pk, "filter": "remaining"}
        )
        assert nav_data[0]["href"] == expected_remaining_url
        assert not nav_data[0]["current"]

        assert nav_data[1]["label"] == "Checked in"
        assert nav_data[1]["count"] == 3
        expected_checked_in_url = reverse(
            "clinics:show_checked_in", kwargs={"pk": clinic_pk, "filter": "checked_in"}
        )
        assert nav_data[1]["href"] == expected_checked_in_url
        assert nav_data[1]["current"]

        assert nav_data[2]["label"] == "In progress"
        assert nav_data[2]["count"] == 2
        expected_in_progress_url = reverse(
            "clinics:show_in_progress",
            kwargs={"pk": clinic_pk, "filter": "in_progress"},
        )
        assert nav_data[2]["href"] == expected_in_progress_url
        assert not nav_data[2]["current"]

        assert nav_data[3]["label"] == "Complete"
        assert nav_data[3]["count"] == 2
        expected_complete_url = reverse(
            "clinics:show_complete", kwargs={"pk": clinic_pk, "filter": "complete"}
        )
        assert nav_data[3]["href"] == expected_complete_url
        assert not nav_data[3]["current"]

        assert nav_data[4]["label"] == "All"
        assert nav_data[4]["count"] == 10
        expected_all_url = reverse(
            "clinics:show_all", kwargs={"pk": clinic_pk, "filter": "all"}
        )
        assert nav_data[4]["href"] == expected_all_url
        assert not nav_data[4]["current"]
