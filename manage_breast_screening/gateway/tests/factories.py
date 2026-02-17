from factory.declarations import Sequence, SubFactory
from factory.django import DjangoModelFactory

from .. import models


class GatewayActionFactory(DjangoModelFactory):
    class Meta:
        model = models.GatewayAction

    appointment = SubFactory(
        "manage_breast_screening.participants.tests.factories.AppointmentFactory"
    )
    type = models.GatewayActionType.WORKLIST_CREATE
    payload = {}
    status = models.GatewayActionStatus.PENDING
    accession_number = Sequence(lambda n: f"ACC20240601{n:04d}")
    sent_at = None
