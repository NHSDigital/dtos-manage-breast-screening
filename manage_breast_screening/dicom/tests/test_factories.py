import pytest

from ..models import BreastOpinions, Opinions
from .factories import ReadingFactory, ReadingSessionFactory


@pytest.mark.django_db
def test_technical_recall_trait():
    opinion = ReadingFactory(technical_recall=True)
    assert opinion.opinion == Opinions.TECHNICAL_RECALL
    assert opinion.retake_requests.count() == 1

    retake_request = opinion.retake_requests.first()
    assert retake_request.view_position == "MLO"
    assert retake_request.laterality == "R"


@pytest.mark.django_db
def test_recall_trait():
    opinion = ReadingFactory(recall=True)
    assert opinion.opinion == Opinions.RECALL
    assert (
        opinion.recall_for_assessment_details.right_breast_opinion
        == BreastOpinions.ABNORMAL
    )
    assert (
        opinion.recall_for_assessment_details.left_breast_opinion
        == BreastOpinions.NORMAL
    )


@pytest.mark.django_db
def test_reading_session():
    session = ReadingSessionFactory()
    assert session.items.count() == 1
