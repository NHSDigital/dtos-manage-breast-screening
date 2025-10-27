from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from manage_breast_screening.notifications.presenters.personalisation_presenter import (
    PersonalisationPresenter,
)
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
    ClinicFactory,
)


@pytest.mark.django_db
class TestPersonalisationPresenter:
    def test_present(self):
        appointment = AppointmentFactory(
            starts_at=datetime(2025, 10, 13, 15, 15, tzinfo=ZoneInfo("Europe/London")),
            clinic=ClinicFactory(
                code="MDSVH",
                bso_code="MBD",
                name="BREAST SCREENING UNIT",
                address_line_1="Victoria Health Centre",
                address_line_2="5 Suffrage Street",
                address_line_3="off Windmill Lane",
                address_line_4="Smethwick",
                address_line_5="West Midlands",
                postcode="B66 3PZ",
            ),
        )
        subject = PersonalisationPresenter(appointment).present()

        assert subject["appointment_date"] == "Monday 13 October 2025"
        assert subject["appointment_time"] == "3:15pm"
        assert subject["appointment_clinic_name"] == "Breast Screening Unit"
        assert subject["appointment_location_address"] == (
            "Victoria Health Centre, 5 Suffrage Street, Off Windmill Lane, Smethwick, West Midlands, B66 3PZ"
        )
        assert subject["appointment_location_description"] == "Off Windmill Lane"
        assert (
            subject["appointment_location_url"]
            == "https://www.google.com/maps/search/B66+3PZ"
        )
        assert subject["BSO_email_address"] == "swb-tr.cswbreastscreening@nhs.net"
        assert subject["BSO_phone_number"] == "0121 507 4967"
        assert subject["appointment_location_address1"] == "Victoria Health Centre"
        assert subject["appointment_location_address2"] == "5 Suffrage Street"
        assert subject["appointment_location_address3"] == "Off Windmill Lane"
        assert subject["appointment_location_address4"] == "Smethwick"
        assert subject["appointment_location_address5"] == "West Midlands"
        assert subject["appointment_location_postcode"] == "B66 3PZ"

    def test_present_with_null_values(self):
        appointment = AppointmentFactory(
            starts_at=datetime(2025, 10, 13, 9, 5, tzinfo=ZoneInfo("Europe/London")),
            clinic=ClinicFactory(
                code="NOPE",
                bso_code="MBD",
                address_line_1="VICTORIA HEALTH CENTRE",
                address_line_2="5 Suffrage Street",
                address_line_3="",
                address_line_4="SMETHWICK",
                address_line_5="",
                postcode="b66 3pz",
            ),
        )
        subject = PersonalisationPresenter(appointment).present()

        assert subject["appointment_date"] == "Monday 13 October 2025"
        assert subject["appointment_time"] == "9:05am"
        assert subject["appointment_location_address"] == (
            "Victoria Health Centre, 5 Suffrage Street, Smethwick, B66 3PZ"
        )
        assert subject["appointment_location_address1"] == "Victoria Health Centre"
        assert subject["appointment_location_address2"] == "5 Suffrage Street"
        assert subject["appointment_location_address3"] == ""
        assert subject["appointment_location_address4"] == "Smethwick"
        assert subject["appointment_location_postcode"] == "B66 3PZ"
        assert subject["appointment_location_description"] == ""
        assert subject["appointment_location_url"] == ""
