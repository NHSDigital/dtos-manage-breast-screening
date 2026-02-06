import re
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
import time_machine

from manage_breast_screening.gateway.models import (
    GatewayAction,
    GatewayActionStatus,
    GatewayActionType,
)
from manage_breast_screening.gateway.relay_service import RelayService
from manage_breast_screening.gateway.worklist_item_service import WorklistItemService
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from .factories import RelayFactory


@pytest.mark.django_db
@patch.object(RelayService, "send_action")
class TestWorklistItemService:
    def test_create_returns_gateway_action(self, _):
        appointment = AppointmentFactory()
        RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)

        assert isinstance(action, GatewayAction)
        assert action.pk is not None
        assert action.status == GatewayActionStatus.PENDING
        assert action.type == GatewayActionType.WORKLIST_CREATE
        assert action.appointment == appointment

    @time_machine.travel("2025-06-15 10:30:00", tick=False)
    def test_accession_number_format(self, _):
        appointment = AppointmentFactory()
        RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)

        assert re.match(r"^ACC20250615[A-F0-9]{4}$", action.accession_number)

    def test_send_action_is_called(self, mock_send_action):
        appointment = AppointmentFactory()
        relay = RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)

        mock_send_action.assert_called_once_with(relay, action)

    def test_no_relay_does_not_create_action(self, mock_send_action):
        appointment = AppointmentFactory()

        action = WorklistItemService.create(appointment)

        assert action is None
        mock_send_action.assert_not_called()

    def test_payload_has_action_id(self, _):
        appointment = AppointmentFactory()
        RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)
        participant = appointment.participant

        assert action.payload["action_id"] == str(action.id)
        assert action.payload["action_type"] == "worklist.create_item"
        worklist_item = action.payload["parameters"]["worklist_item"]
        assert worklist_item["accession_number"] == action.accession_number
        assert worklist_item["participant"]["nhs_number"] == participant.nhs_number
        assert worklist_item["procedure"]["modality"] == "MG"

    def test_payload_has_participant_name_in_dicom_format(self, _):
        appointment = AppointmentFactory(first_name="Jane", last_name="Smith")
        RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)

        worklist_item = action.payload["parameters"]["worklist_item"]
        assert worklist_item["participant"]["name"] == "SMITH^JANE"

    def test_payload_has_participant_birth_date(self, _):
        appointment = AppointmentFactory()
        appointment.participant.date_of_birth = date(1975, 3, 21)
        appointment.participant.save()
        RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)

        worklist_item = action.payload["parameters"]["worklist_item"]
        assert worklist_item["participant"]["birth_date"] == "19750321"

    def test_payload_defaults_sex_to_f_when_missing(self, _):
        appointment = AppointmentFactory()
        appointment.participant.gender = ""
        appointment.participant.save()
        RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)

        worklist_item = action.payload["parameters"]["worklist_item"]
        assert worklist_item["participant"]["sex"] == "F"

    def test_payload_has_scheduled_date_from_clinic_slot(self, _):
        appointment = AppointmentFactory(
            starts_at=datetime(2025, 7, 10, 14, 30, tzinfo=timezone.utc)
        )
        RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)

        worklist_item = action.payload["parameters"]["worklist_item"]
        assert worklist_item["scheduled"]["date"] == "20250710"
        assert worklist_item["scheduled"]["time"] == "143000"
