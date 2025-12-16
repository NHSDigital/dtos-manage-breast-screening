from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from factory import LazyAttribute, Trait, post_generation
from factory.declarations import RelatedFactoryList, Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from manage_breast_screening.auth.models import Role
from manage_breast_screening.clinics import models

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("nhs_uid",)

    nhs_uid = Sequence(lambda n: f"user_{n}")
    email = Sequence(lambda n: f"user{n}@example.com")
    first_name = Sequence(lambda n: f"First{n}")
    last_name = Sequence(lambda n: f"Last{n}")


class ProviderFactory(DjangoModelFactory):
    class Meta:
        model = models.Provider
        django_get_or_create = ("name",)

    name = Sequence(lambda n: "provider %d" % n)


class SettingFactory(DjangoModelFactory):
    class Meta:
        model = models.Setting
        django_get_or_create = ("name",)

    name = Sequence(lambda n: "setting %d" % n)
    provider = SubFactory(ProviderFactory)


class ClinicStatusFactory(DjangoModelFactory):
    class Meta:
        model = models.ClinicStatus

    clinic = None
    state = models.ClinicStatus.SCHEDULED


class ClinicFactory(DjangoModelFactory):
    class Meta:
        model = models.Clinic
        django_get_or_create = ("starts_at", "ends_at", "setting")
        skip_postgeneration_save = True

    type = FuzzyChoice(models.Clinic.TYPE_CHOICES)
    risk_type = FuzzyChoice(models.Clinic.RISK_TYPE_CHOICES)
    starts_at = Sequence(
        lambda n: datetime(2025, 1, 1, 9, tzinfo=timezone.utc) + timedelta(hours=n)
    )
    ends_at = LazyAttribute(lambda o: o.starts_at + timedelta(minutes=30))
    setting = SubFactory(SettingFactory)

    # Create a status by default
    statuses = RelatedFactoryList(
        ClinicStatusFactory, size=1, factory_related_name="clinic"
    )

    # Allow passing an explicit status
    # e.g. `current_status=ClinicStatus.IN_PROGRESS`
    @post_generation
    def current_status(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return

        obj.statuses.add(ClinicStatusFactory.create(state=extracted, clinic=obj))


class ClinicSlotFactory(DjangoModelFactory):
    class Meta:
        model = models.ClinicSlot

    clinic = SubFactory(ClinicFactory)
    starts_at = Sequence(
        lambda n: datetime(2025, 1, 1, 9, tzinfo=timezone.utc) + timedelta(hours=n)
    )
    starts_at_time = LazyAttribute(lambda o: o.starts_at.time())
    duration_in_minutes = 15


class UserAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = models.UserAssignment

    user = SubFactory(UserFactory)
    provider = SubFactory(ProviderFactory)

    class Params:
        clinical = Trait(roles=[Role.CLINICAL])
        administrative = Trait(roles=[Role.ADMINISTRATIVE])
