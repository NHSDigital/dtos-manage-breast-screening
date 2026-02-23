import uuid

from factory.declarations import Sequence, SubFactory
from factory.django import DjangoModelFactory

from .. import models


class StudyFactory(DjangoModelFactory):
    class Meta:
        model = models.Study

    study_instance_uid = Sequence(lambda n: f"STUDY{n:04d}")
    source_message_id = uuid.uuid4()
    patient_id = Sequence(lambda n: f"999{n:07d}")
    date_and_time = None
    description = "Test Study"


class SeriesFactory(DjangoModelFactory):
    class Meta:
        model = models.Series

    series_instance_uid = Sequence(lambda n: f"SERIES{n:04d}")
    study = SubFactory(StudyFactory)
    modality = "MG"
    series_number = Sequence(lambda n: n)


class ImageFactory(DjangoModelFactory):
    class Meta:
        model = models.Image

    sop_instance_uid = Sequence(lambda n: f"SOP{n:04d}")
    series = SubFactory("manage_breast_screening.dicom.tests.factories.SeriesFactory")
    instance_number = Sequence(lambda n: n)
    laterality = "L"
    view_position = "CC"
