from functools import cached_property

from django.urls import reverse

from ..core.utils.date_formatting import format_date, format_time_range
from ..core.utils.string_formatting import sentence_case
from ..mammograms.presenters import AppointmentPresenter
from .models import ClinicStatus


class ClinicsPresenter:
    def __init__(self, filtered_clinics, filter, counts_by_filter):
        self.clinics = [ClinicPresenter(clinic) for clinic in filtered_clinics]
        self.counts_by_filter = counts_by_filter
        self.filter = filter

    @cached_property
    def heading(self):
        if self.filter == "today":
            return "Today’s clinics"
        elif self.filter == "upcoming":
            return "Upcoming clinics"
        elif self.filter == "completed":
            return "Completed clinics this week"
        else:
            return "All clinics this week"


class ClinicPresenter:
    STATUS_COLORS = {
        ClinicStatus.SCHEDULED: "blue",  # default blue
        ClinicStatus.IN_PROGRESS: "blue",
        ClinicStatus.CLOSED: "grey",
    }

    def __init__(self, clinic):
        self._clinic = clinic
        self.pk = clinic.pk
        self.starts_at = format_date(clinic.starts_at)
        self.session_type = clinic.session_type().capitalize()
        self.number_of_slots = clinic.clinic_slots.count()
        self.location_name = sentence_case(clinic.setting.name)
        self.time_range = format_time_range(clinic.time_range())
        self.type = clinic.get_type_display()
        self.risk_type = clinic.get_risk_type_display()

    @cached_property
    def state(self):
        status = self._clinic.current_status
        value = status.state
        text = status.get_state_display()

        return {
            "text": text,
            "classes": "nhsuk-tag--" + self.STATUS_COLORS[value],
        }

    @cached_property
    def setting_name(self):
        return self._clinic.setting.name


class AppointmentListPresenter:
    def __init__(self, clinic_pk, appointments, filter, counts_by_filter):
        self.appointments = [
            AppointmentPresenter(appointment) for appointment in appointments
        ]
        self.filter = filter
        self.counts_by_filter = counts_by_filter
        self.clinic_pk = clinic_pk

    @cached_property
    def secondary_nav_data(self):
        filters = [
            {
                "label": "Remaining",
                "filter": "remaining",
            },
            {
                "label": "Checked in",
                "filter": "checked_in",
            },
            {
                "label": "Complete",
                "filter": "complete",
            },
            {
                "label": "All",
                "filter": "all",
            },
        ]
        nav = []
        for filter in filters:
            filter_label = filter["label"]
            filter_identifier = filter["filter"]
            count = self.counts_by_filter.get(filter_identifier)
            nav.append(
                {
                    "label": filter_label,
                    "count": count,
                    "href": reverse(
                        "clinics:show_" + filter_identifier,
                        kwargs={"pk": self.clinic_pk},
                    ),
                    "current": filter_identifier == self.filter,
                }
            )
        return nav
