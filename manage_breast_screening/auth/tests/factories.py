from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from factory.declarations import Sequence
from factory.django import DjangoModelFactory
from factory.helpers import post_generation

from manage_breast_screening.auth.rules import Role


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ("first_name", "last_name")
        skip_postgeneration_save = True

    nhs_uid = Sequence(lambda n: "alice%d" % n)
    first_name = Sequence(lambda n: "alice%d" % n)
    last_name = "Lastname"

    @post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.groups.set(extracted)

        if kwargs.get("administrative"):
            self.groups.add(Group.objects.get(name=Role.ADMINISTRATIVE))

        if kwargs.get("clinical"):
            self.groups.add(Group.objects.get(name=Role.CLINICAL))
