"""
Define rules and permissions for access control.

This file is automatically imported by rules.apps.AutodiscoverRulesConfig
"""

import rules

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.auth.rules import is_clinical
from manage_breast_screening.participants.models import AppointmentStatus


@rules.predicate
def can_start_appointment(user, appointment):
    if not is_clinical(user):
        return False

    return appointment and appointment.current_status.state in (
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CHECKED_IN,
    )


rules.add_perm(Permission.VIEW_MAMMOGRAM_APPOINTMENT, is_clinical)
rules.add_perm(Permission.START_MAMMOGRAM_APPOINTMENT, can_start_appointment)
