from datetime import datetime
from datetime import timezone as tz

import pytest
import time_machine
from django.core.exceptions import ValidationError
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.auth.models import Role
from manage_breast_screening.clinics import models

from .factories import (
    ClinicFactory,
    ClinicSlotFactory,
    ProviderFactory,
    UserAssignmentFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_clinic_current_status():
    clinic = ClinicFactory.create(current_status=models.ClinicStatus.SCHEDULED)
    clinic.statuses.create(state=models.ClinicStatus.CANCELLED)
    assert clinic.statuses.first().state == models.ClinicStatus.CANCELLED
    assert clinic.current_status.state == models.ClinicStatus.CANCELLED


@pytest.mark.django_db
@time_machine.travel(datetime(2025, 1, 1, 10, tzinfo=tz.utc))
def test_date_filtering():
    current = ClinicFactory.create(starts_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc))
    future = ClinicFactory.create(starts_at=datetime(2025, 1, 2, 9, tzinfo=tz.utc))
    past = ClinicFactory.create(starts_at=datetime(2024, 1, 1, 9, tzinfo=tz.utc))

    assertQuerySetEqual(
        models.Clinic.objects.all(), {current, future, past}, ordered=False
    )
    assertQuerySetEqual(models.Clinic.objects.today(), {current}, ordered=False)
    assertQuerySetEqual(models.Clinic.objects.upcoming(), {future}, ordered=False)


@pytest.mark.django_db
@time_machine.travel(datetime(2025, 1, 1, 10, tzinfo=tz.utc))
def test_completed_filtering_by_date_and_status():
    past_closed = ClinicFactory.create(
        starts_at=datetime(2024, 12, 31, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 31, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.CLOSED,
    )

    past_cancelled = ClinicFactory.create(
        starts_at=datetime(2024, 12, 30, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 30, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.CANCELLED,
    )

    # Past clinic with SCHEDULED status - should be excluded
    ClinicFactory.create(
        starts_at=datetime(2024, 12, 29, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 29, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.SCHEDULED,
    )
    completed = models.Clinic.objects.completed()

    assertQuerySetEqual(completed, [past_closed, past_cancelled], ordered=False)


@pytest.mark.django_db
@time_machine.travel(datetime(2025, 1, 1, 10, tzinfo=tz.utc))
def test_completed_ordering_by_ends_at():
    clinic1 = ClinicFactory.create(
        starts_at=datetime(2024, 12, 31, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 31, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.CLOSED,
    )
    clinic2 = ClinicFactory.create(
        starts_at=datetime(2024, 12, 30, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 30, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.CLOSED,
    )
    clinic3 = ClinicFactory.create(
        starts_at=datetime(2024, 12, 29, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 29, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.CLOSED,
    )

    completed = models.Clinic.objects.completed()
    assertQuerySetEqual(completed, [clinic1, clinic2, clinic3])


@pytest.mark.django_db
def test_clean_clinic_slots():
    clinic = ClinicFactory.build(starts_at=datetime(2024, 12, 29, 9, tzinfo=tz.utc))
    clinic_slot = ClinicSlotFactory.build(
        starts_at=datetime(2024, 12, 26, 9, tzinfo=tz.utc),
        duration_in_minutes=30,
        clinic=clinic,
    )
    with pytest.raises(ValidationError):
        clinic_slot.clean()


@time_machine.travel(datetime(2025, 1, 1, 10, tzinfo=tz.utc))
@pytest.mark.django_db
def test_last_seven_days_all_filtering():
    _clinic1 = ClinicFactory.create(
        starts_at=datetime(2024, 12, 1, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 1, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.CLOSED,
    )
    _clinic2 = ClinicFactory.create(
        starts_at=datetime(2024, 12, 2, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 2, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.CLOSED,
    )
    clinic3 = ClinicFactory.create(
        starts_at=datetime(2024, 12, 29, 9, tzinfo=tz.utc),
        ends_at=datetime(2024, 12, 29, 17, tzinfo=tz.utc),
        current_status=models.ClinicStatus.CLOSED,
    )

    last_seven_days_clinics = models.Clinic.objects.last_seven_days()
    assertQuerySetEqual(last_seven_days_clinics, [clinic3])


class TestUserAssignment:
    def test_str(self):
        user = UserFactory.build(first_name="John", last_name="Doe")
        provider = ProviderFactory.build(name="Test Provider")
        assignment = UserAssignmentFactory.build(user=user, provider=provider)
        assert str(assignment) == "John Doe → Test Provider"

    @pytest.mark.django_db
    def test_unique_constraint(self):
        user = UserFactory()
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider)

        with pytest.raises(Exception):
            UserAssignmentFactory(user=user, provider=provider)

    @pytest.mark.django_db
    def test_related_names(self):
        user = UserFactory()
        provider = ProviderFactory()
        assignment = UserAssignmentFactory(user=user, provider=provider)

        assert assignment in user.assignments.all()
        assert assignment in provider.assignments.all()

    @pytest.mark.django_db
    def test_roles_ordering(self):
        """Test that roles are sorted alphabetically for consistent ordering."""
        user = UserFactory()
        provider = ProviderFactory()

        # Create assignment with roles in reverse alphabetical order
        assignment = UserAssignmentFactory(
            user=user,
            provider=provider,
            roles=[Role.CLINICAL.value, Role.ADMINISTRATIVE.value],
        )

        assert assignment.roles == [Role.ADMINISTRATIVE.value, Role.CLINICAL.value]

    @pytest.mark.django_db
    def test_roles_single_role(self):
        """Test that single role works correctly."""
        user = UserFactory()
        provider = ProviderFactory()

        assignment = UserAssignmentFactory(
            user=user, provider=provider, roles=[Role.CLINICAL.value]
        )

        assert assignment.roles == [Role.CLINICAL.value]

    @pytest.mark.django_db
    def test_roles_duplicate_values(self):
        """Test that duplicate roles are deduplicated and sorted on save."""
        user = UserFactory()
        provider = ProviderFactory()

        assignment = UserAssignmentFactory(
            user=user,
            provider=provider,
            roles=[Role.CLINICAL.value, Role.CLINICAL.value, Role.ADMINISTRATIVE.value],
        )

        # Should be sorted and deduplicated
        assert assignment.roles == [
            Role.ADMINISTRATIVE.value,
            Role.CLINICAL.value,
        ]
