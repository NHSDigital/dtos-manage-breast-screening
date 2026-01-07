from django.contrib.auth import get_user_model
from factory.declarations import Sequence
from factory.django import DjangoModelFactory

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("nhs_uid",)

    nhs_uid = Sequence(lambda n: f"user_{n}")
    email = Sequence(lambda n: f"user{n}@example.com")
    first_name = Sequence(lambda n: f"First{n}")
    last_name = Sequence(lambda n: f"Last{n}")
