import uuid

from factory.declarations import RelatedFactory, Sequence, SubFactory, Trait
from factory.django import DjangoModelFactory, FileField
from factory.helpers import post_generation

from manage_breast_screening.users.tests.factories import UserFactory

from .. import models


class StudyFactory(DjangoModelFactory):
    class Meta:
        model = models.Study

    study_instance_uid = Sequence(lambda n: f"STUDY{n:04d}")
    source_message_id = uuid.uuid4()
    patient_id = Sequence(lambda n: f"999{n:07d}")
    date_and_time = None
    description = "Test Study"


class StudyWithImagesFactory(StudyFactory):
    class Meta:
        skip_postgeneration_save = True

    @post_generation
    def num_images(obj, created, extracted, **kwargs):
        if not created:
            return

        if not extracted:
            extracted = 1

        for _ in range(extracted):
            ImageFactory(series__study=obj)


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
    image_file = FileField(filename="image.jpg")


class RecallForAssessmentDetailsFactory(DjangoModelFactory):
    class Meta:
        model = models.RecallForAssessmentDetails

    right_breast_opinion = models.BreastOpinions.ABNORMAL
    left_breast_opinion = models.BreastOpinions.NORMAL


class RetakeRequestFactory(DjangoModelFactory):
    class Meta:
        model = models.RetakeRequest

    laterality = "R"
    view_position = "MLO"


class ReadingFactory(DjangoModelFactory):
    class Meta:
        model = models.Reading
        skip_postgeneration_save = True

    study = SubFactory(StudyWithImagesFactory)
    reader = SubFactory(UserFactory)
    opinion = models.Opinions.NORMAL

    class Params:
        normal = Trait(opinion=models.Opinions.NORMAL)
        technical_recall = Trait(
            opinion=models.Opinions.TECHNICAL_RECALL,
            retake_request_1=RelatedFactory(
                RetakeRequestFactory, factory_related_name="reading"
            ),
        )
        recall = Trait(
            opinion=models.Opinions.RECALL,
            recall_for_assessment_details=RelatedFactory(
                RecallForAssessmentDetailsFactory, factory_related_name="reading"
            ),
        )


class ReadingSessionItemFactory(DjangoModelFactory):
    class Meta:
        model = models.ReadingSessionItem

    study = SubFactory(StudyFactory)
    order = Sequence(lambda i: i)


class ReadingSessionFactory(DjangoModelFactory):
    class Meta:
        model = models.ReadingSession
        skip_postgeneration_save = True

    reader = SubFactory(UserFactory)
    session_size = 50
    item_1 = RelatedFactory(ReadingSessionItemFactory, factory_related_name="session")
