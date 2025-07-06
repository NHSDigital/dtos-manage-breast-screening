import pytest
from django.test import RequestFactory

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.participants.models import Participant
from manage_breast_screening.participants.tests.factories import ParticipantFactory

from ..factories import UserFactory


@pytest.mark.django_db
class TestAuditor:
    def test_audit_create(self):
        auditor = Auditor(system_update_id="test")
        participant = ParticipantFactory.create()

        log = auditor.audit_create(participant)

        assert log.system_update_id == "test"
        assert log.operation == "create"
        assert log.content_type.model_class() == Participant
        assert log.object_id == participant.pk
        assert log.snapshot == {
            "first_name": participant.first_name,
            "last_name": participant.last_name,
            "gender": participant.gender,
            "nhs_number": participant.nhs_number,
            "phone": participant.phone,
            "email": participant.email,
            "date_of_birth": participant.date_of_birth,
            "ethnic_background_id": participant.ethnic_background_id,
            "any_other_background_details": participant.any_other_background_details,
            "risk_level": participant.risk_level,
            "extra_needs": participant.extra_needs,
        }

    def test_audit_update(self):
        auditor = Auditor(system_update_id="test")
        participant = ParticipantFactory.create(first_name="ABC")
        auditor.audit_create(participant)

        participant.first_name = "DEF"
        participant.save()

        log = auditor.audit_update(participant)

        assert log.system_update_id == "test"
        assert log.operation == "update"
        assert log.content_type.model_class() == Participant
        assert log.object_id == participant.pk
        assert log.snapshot["first_name"] == "DEF"

    def test_audit_delete(self):
        auditor = Auditor(system_update_id="test")
        participant = ParticipantFactory.create()
        pk = participant.pk

        # audit_delete must be called before the record is deleted
        log = auditor.audit_delete(participant)

        participant.delete()
        log.refresh_from_db()

        assert log.system_update_id == "test"
        assert log.operation == "delete"
        assert log.content_type.model_class() == Participant
        assert log.object_id == pk

    def test_audit_bulk_create(self):
        auditor = Auditor(system_update_id="test")
        a = ParticipantFactory.build()
        b = ParticipantFactory.build()
        Participant.objects.bulk_create([a, b])

        logs = auditor.audit_bulk_create([a, b])
        assert len(logs) == 2
        assert all(log.system_update_id == "test" for log in logs)
        assert all(log.operation == "create" for log in logs)
        assert all(log.content_type.model_class() == Participant for log in logs)
        assert logs[0].object_id == a.pk
        assert logs[1].object_id == b.pk
        assert logs[0].snapshot == {
            "first_name": a.first_name,
            "last_name": a.last_name,
            "gender": a.gender,
            "nhs_number": a.nhs_number,
            "phone": a.phone,
            "email": a.email,
            "date_of_birth": a.date_of_birth,
            "ethnic_background_id": a.ethnic_background_id,
            "any_other_background_details": a.any_other_background_details,
            "risk_level": a.risk_level,
            "extra_needs": a.extra_needs,
        }
        assert logs[1].snapshot == {
            "first_name": b.first_name,
            "last_name": b.last_name,
            "gender": b.gender,
            "nhs_number": b.nhs_number,
            "phone": b.phone,
            "email": b.email,
            "date_of_birth": b.date_of_birth,
            "ethnic_background_id": b.ethnic_background_id,
            "any_other_background_details": b.any_other_background_details,
            "risk_level": b.risk_level,
            "extra_needs": b.extra_needs,
        }

    def test_audit_bulk_update(self):
        auditor = Auditor(system_update_id="test")
        a = ParticipantFactory.create(first_name="abc")
        b = ParticipantFactory.create(first_name="def")
        a.first_name = "A"
        b.first_name = "B"
        Participant.objects.bulk_update([a, b], fields=["first_name"])

        logs = auditor.audit_bulk_update([a, b])
        assert len(logs) == 2
        assert all(log.system_update_id == "test" for log in logs)
        assert all(log.operation == "update" for log in logs)
        assert all(log.content_type.model_class() == Participant for log in logs)
        assert logs[0].object_id == a.pk
        assert logs[1].object_id == b.pk
        assert logs[0].snapshot == {
            "first_name": "A",
            "last_name": a.last_name,
            "gender": a.gender,
            "nhs_number": a.nhs_number,
            "phone": a.phone,
            "email": a.email,
            "date_of_birth": a.date_of_birth,
            "ethnic_background_id": a.ethnic_background_id,
            "any_other_background_details": a.any_other_background_details,
            "risk_level": a.risk_level,
            "extra_needs": a.extra_needs,
        }
        assert logs[1].snapshot == {
            "first_name": "B",
            "last_name": b.last_name,
            "gender": b.gender,
            "nhs_number": b.nhs_number,
            "phone": b.phone,
            "email": b.email,
            "date_of_birth": b.date_of_birth,
            "ethnic_background_id": b.ethnic_background_id,
            "any_other_background_details": b.any_other_background_details,
            "risk_level": b.risk_level,
            "extra_needs": b.extra_needs,
        }

    def test_audit_bulk_delete(self):
        auditor = Auditor(system_update_id="test")
        a = ParticipantFactory.create()
        b = ParticipantFactory.create()
        pks = [a.pk, b.pk]

        logs = auditor.audit_bulk_delete(Participant.objects.all())
        assert len(logs) == 2
        assert all(log.system_update_id == "test" for log in logs)
        assert all(log.operation == "delete" for log in logs)
        assert all(log.content_type.model_class() == Participant for log in logs)
        assert logs[0].object_id == pks[0]
        assert logs[1].object_id == pks[1]
        assert logs[0].snapshot == {}
        assert logs[1].snapshot == {}

    def test_from_request(self):
        user = UserFactory.create()
        request = RequestFactory().get("/clinics")
        request.user = user

        auditor = Auditor.from_request(request)
        log = auditor.audit_create(user)
        assert log.actor == user
