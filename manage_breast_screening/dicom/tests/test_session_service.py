import pytest
from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef

from manage_breast_screening.dicom.tests.factories import StudyFactory

from ..models import ReadingSession, ReadingSessionItem, Study


class NoImagesToRead(Exception):
    pass


class SessionService:
    def __init__(self, reader, provider):
        self.reader = reader
        self.provider = provider

    @transaction.atomic
    def create(self):
        # TODO: scope to provider
        study_queue = (
            Study.objects.filter(
                ~Exists(ReadingSessionItem.objects.filter(study=OuterRef("pk")))
            )
            .order_by("date_and_time", "id")
            .select_for_update(skip_locked=True)
        )
        study = study_queue.first()
        if study is None:
            raise NoImagesToRead

        session = ReadingSession.objects.create(
            reader=self.reader, session_size=settings.READING_SESSION_DEFAULT_SIZE
        )
        session.items.create(session=session, study=study, order=1)
        return session


class TestSessionService:
    @pytest.mark.django_db
    def test_create_with_one_item(self, user, current_provider):
        assert Study.objects.count() == 0
        study = StudyFactory.create()

        session = SessionService(user, current_provider).create()

        assert session.items.count() == 1
        assert session.items.first().study == study


# @pytest.mark.django_db(transaction=True)
# class TestSessionServiceConcurrentUse:
#     def test_concurrent_claiming_of_items(
#         self,
#         user,
#         current_provider,
#     ):
#         studies = StudyFactory.create_batch(100)
#         study_ids = [study.id for study in studies]
#         executor = ThreadPoolExecutor(max_workers=2)

#         def create_session(i):
#             return SessionService(user, current_provider).create()

#         sessions = list(executor.map(create_session, range(100)))
#         assigned_study_ids = [
#             session.items.first().study.id for session in sessions if session
#         ]
#         assert sorted(study_ids) == sorted(assigned_study_ids)
