from factory import Faker
from factory.declarations import (
    SubFactory,
)
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

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
    view_position = FuzzyChoice(choices=["CC", "MLO", "EKLUND"])
    laterality = FuzzyChoice(choices=["L", "R"])
    count = FuzzyChoice(choices=list(range(1, 21)))

    class Meta:
        model = Series
        django_get_or_create = ("study", "view_position", "laterality")
