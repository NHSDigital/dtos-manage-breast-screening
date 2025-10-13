from datetime import datetime
from datetime import timezone as tz

import pytest
import time_machine
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.auth.models import Role
from manage_breast_screening.clinics import models

from .factories import (
    ClinicFactory,
    ProviderFactory,
    SettingFactory,
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
def test_status_filtering():
    provider = ProviderFactory.create()
    setting = SettingFactory.create(provider=provider)
    current = ClinicFactory.create(
        setting=setting, starts_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc)
    )
    future = ClinicFactory.create(
        setting=setting, starts_at=datetime(2025, 1, 2, 9, tzinfo=tz.utc)
    )
    past = ClinicFactory.create(
        setting=setting, starts_at=datetime(2024, 1, 1, 9, tzinfo=tz.utc)
    )
    ClinicFactory.create()  # Different provider

    provider_scoped = models.Clinic.objects.for_provider(provider)

    assertQuerySetEqual(provider_scoped.all(), {current, future, past}, ordered=False)
    assertQuerySetEqual(provider_scoped.today(), {current}, ordered=False)
    assertQuerySetEqual(provider_scoped.upcoming(), {future}, ordered=False)
    assertQuerySetEqual(provider_scoped.completed(), {past}, ordered=False)


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
