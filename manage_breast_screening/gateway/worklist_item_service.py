"""Gateway action services."""

import logging
import uuid
from datetime import datetime, timezone

from django.db import IntegrityError

from manage_breast_screening.dicom.models import Image
from manage_breast_screening.participants.models import Appointment

from .models import GatewayAction, GatewayActionStatus, GatewayActionType, Relay
from .relay_service import RelayService

logger = logging.getLogger(__name__)


def get_images_for_appointment(appointment: Appointment):
    """
    Get all DICOM images for an appointment via its GatewayAction.
    """
    action = appointment.gateway_actions.filter(
        type=GatewayActionType.WORKLIST_CREATE
    ).first()

    if not action:
        return Image.objects.none()

    return (
        Image.objects.filter(series__study__source_message_id=str(action.id))
        .select_related("series__study")
        .order_by("series__series_number", "instance_number")
    )


class GatewayActionAlreadyExistsError(Exception):
    """Raised when a gateway action already exists for the appointment."""

    pass


class WorklistItemService:
    """Service for creating worklist item actions for the gateway."""

    def __init__(self, appointment: Appointment):
        self.appointment = appointment
        self.participant = appointment.participant

    @classmethod
    def create(cls, appointment: Appointment) -> GatewayAction:
        """
        Create a worklist item action for the given appointment.

        Returns the GatewayAction with status PENDING.
        The action will be picked up and sent by the relay sender service.
        """
        service = cls(appointment)
        return service._create_action()

    def _generate_accession_number(self) -> str:
        """Generate unique accession number (max 16 chars per DICOM SH limit)."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:4].upper()
        return f"ACC{timestamp}{random_suffix}"

    def _build_payload(self, action_id: uuid.UUID, accession_number: str) -> dict:
        """Build the worklist create payload."""
        participant = self.participant
        appointment = self.appointment

        # Format name: LAST^FIRST
        participant_name = (
            f"{participant.last_name.upper()}^{participant.first_name.upper()}"
        )

        scheduled_datetime = appointment.clinic_slot.starts_at
        scheduled_date = scheduled_datetime.strftime("%Y%m%d")
        scheduled_time = scheduled_datetime.strftime("%H%M%S")

        return {
            "schema_version": 1,
            "action_id": str(action_id),
            "action_type": GatewayActionType.WORKLIST_CREATE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_system": "manage-breast-screening",
            "source_reference": {
                "appointment_id": str(appointment.pk),
                "participant_id": participant.nhs_number,
            },
            "parameters": {
                "worklist_item": {
                    "accession_number": accession_number,
                    "participant": {
                        "nhs_number": participant.nhs_number,
                        "name": participant_name,
                        "birth_date": participant.date_of_birth.strftime("%Y%m%d"),
                        "sex": participant.gender[0].upper()
                        if participant.gender
                        else "F",
                    },
                    "scheduled": {
                        "date": scheduled_date,
                        "time": scheduled_time,
                    },
                    "procedure": {
                        "modality": "MG",
                        "study_description": "Screening Mammography",
                    },
                }
            },
        }

    def _create_action(self) -> GatewayAction | None:
        """Create and persist the gateway action."""
        relay = Relay.for_provider(self.appointment.provider)

        if not relay:
            logger.info(
                "No relay found for provider %s, skipping create gateway action",
                self.appointment.provider.name,
            )
            return None

        action_id = uuid.uuid4()
        accession_number = self._generate_accession_number()
        payload = self._build_payload(action_id, accession_number)

        try:
            action = GatewayAction.objects.create(
                id=action_id,
                appointment=self.appointment,
                type=GatewayActionType.WORKLIST_CREATE,
                accession_number=accession_number,
                payload=payload,
                status=GatewayActionStatus.PENDING,
            )
        except IntegrityError as e:
            raise GatewayActionAlreadyExistsError(
                f"Gateway action already exists for appointment {self.appointment.pk}"
            ) from e

        logger.info(
            f"Created gateway action {action_id} for appointment {self.appointment.pk}"
        )

        try:
            RelayService().send_action(relay, action)
        except Exception as e:
            logger.error(f"Failed to send gateway action {action_id} to relay: {e}")

        return action
