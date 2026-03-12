import pytest
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.clinics.services import get_user_providers
from manage_breast_screening.clinics.tests.factories import (
    ProviderFactory,
    UserAssignmentFactory,
)
from manage_breast_screening.clinics.views import get_user_providers_with_roles


@pytest.mark.django_db
def test_get_user_providers_with_roles(user):
    provider1 = ProviderFactory.create()
    provider2 = ProviderFactory.create()

    UserAssignmentFactory.create(user=user, provider=provider1, clinical=True)
    UserAssignmentFactory.create(user=user, provider=provider2)

    user.is_superuser = False
    assertQuerySetEqual(get_user_providers_with_roles(user), [provider1], ordered=False)

    user.is_superuser = True
    assertQuerySetEqual(
        get_user_providers_with_roles(user), [provider1, provider2], ordered=False
    )


@pytest.mark.django_db
def test_get_user_providers(user):
    provider1 = ProviderFactory.create()
    provider2 = ProviderFactory.create()

    UserAssignmentFactory.create(user=user, provider=provider1)

    user.is_superuser = False
    assertQuerySetEqual(get_user_providers(user), [provider1], ordered=False)

    user.is_superuser = True
    assertQuerySetEqual(
        get_user_providers_with_roles(user), [provider1, provider2], ordered=False
    )
