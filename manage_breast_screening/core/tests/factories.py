from django.contrib.auth import get_user_model
from factory.declarations import Sequence
from factory.django import DjangoModelFactory

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    nhs_uid = Sequence(lambda n: "user%d" % n)
    email = Sequence(lambda n: "user%d@example.com" % n)
    first_name = "Firstname"
    last_name = "Lastname"
