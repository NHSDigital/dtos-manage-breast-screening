import factory
from factory import Faker
from factory.declarations import (
    SubFactory,
)
from factory.django import DjangoModelFactory

from manage_breast_screening.manual_images.models import Series, Study
from manage_breast_screening.participants.tests.factories import AppointmentFactory


class StudyFactory(DjangoModelFactory):
    appointment = SubFactory(AppointmentFactory)
    additional_details = Faker("text", max_nb_chars=200)

    class Meta:
        model = Study
        django_get_or_create = ("appointment",)


class SeriesFactory(DjangoModelFactory):
    study = SubFactory(StudyFactory)
    view_position = "CC"
    laterality = "R"
    count = 1

    class Params:
        rcc = factory.Trait(view_position="CC", laterality="R")
        rmlo = factory.Trait(view_position="MLO", laterality="R")
        right_eklund = factory.Trait(view_position="EKLUND", laterality="R")
        lcc = factory.Trait(view_position="CC", laterality="L")
        lmlo = factory.Trait(view_position="MLO", laterality="L")
        left_eklund = factory.Trait(view_position="EKLUND", laterality="L")

    class Meta:
        model = Series
