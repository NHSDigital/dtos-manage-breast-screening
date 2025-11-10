from django.contrib.auth import get_user_model
from factory.declarations import Sequence
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ("first_name", "last_name")
        skip_postgeneration_save = True

    nhs_uid = Sequence(lambda n: "alice%d" % n)
    first_name = Sequence(lambda n: "Alice%d" % n)
    last_name = "Lastname"
