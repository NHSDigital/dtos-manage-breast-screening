from datetime import datetime
from datetime import timezone as tz

import pytest
import time_machine
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.clinics import models

from .factories import ClinicFactory


@pytest.mark.django_db
def test_clinic_current_status():
    clinic = ClinicFactory.create(current_status=models.ClinicStatus.SCHEDULED)
    clinic.statuses.create(state=models.ClinicStatus.CANCELLED)
    assert clinic.statuses.first().state == models.ClinicStatus.CANCELLED
    assert clinic.current_status.state == models.ClinicStatus.CANCELLED


@pytest.mark.django_db
@time_machine.travel(datetime(2025, 1, 1, 10, tzinfo=tz.utc))
def test_status_filtering():
    current = ClinicFactory.create(starts_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc))
    future = ClinicFactory.create(starts_at=datetime(2025, 1, 2, 9, tzinfo=tz.utc))
    past = ClinicFactory.create(starts_at=datetime(2024, 1, 1, 9, tzinfo=tz.utc))

    assertQuerySetEqual(
        models.Clinic.objects.all(), {current, future, past}, ordered=False
    )
    assertQuerySetEqual(models.Clinic.objects.today(), {current}, ordered=False)
    assertQuerySetEqual(models.Clinic.objects.upcoming(), {future}, ordered=False)
    assertQuerySetEqual(models.Clinic.objects.completed(), {past}, ordered=False)
