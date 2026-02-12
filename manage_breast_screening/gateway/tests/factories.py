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


class RelayFactory(DjangoModelFactory):
    class Meta:
        model = models.Relay

    namespace = Sequence(lambda n: f"myrelay{n}.servicebus.windows.net")
    hybrid_connection_name = Sequence(lambda n: f"hybrid-connection-{n}")
    key_name = "RootManageSharedAccessKey"
    shared_access_key_variable_name = Sequence(lambda n: f"SHARED_ACCESS_KEY_{n}")
    provider = SubFactory(
        "manage_breast_screening.clinics.tests.factories.ProviderFactory"
    )
