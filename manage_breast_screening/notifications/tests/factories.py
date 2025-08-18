import uuid
from datetime import datetime, timedelta

from factory.declarations import Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.helpers import post_generation

from manage_breast_screening.notifications.management.commands.send_message_batch import (
    TZ_INFO,
)

from .. import models


class ClinicFactory(DjangoModelFactory):
    class Meta:
        model = models.Clinic

    code = Sequence(lambda n: f"BU00{n}")
    name = "BREAST CARE UNIT"
    holding_clinic = False


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = models.Appointment

    clinic = SubFactory(ClinicFactory)
    nhs_number = Sequence(lambda n: int("999%06d" % n))
    starts_at = datetime.now(tz=TZ_INFO) + timedelta(weeks=4, days=4)
    status = "B"
    nbss_id = Sequence(lambda n: int("123%06d" % n))


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = models.Message

    appointment = SubFactory(AppointmentFactory)


class MessageBatchFactory(DjangoModelFactory):
    class Meta:
        model = models.MessageBatch
        skip_postgeneration_save = True

    routing_plan_id = str(uuid.uuid4())
    status = "unscheduled"

    @post_generation
    def messages(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for message in extracted:
                self.messages.add(message)


class ChannelStatusFactory(DjangoModelFactory):
    class Meta:
        model = models.ChannelStatus

    channel = "nhsapp"
    description = "Read"
    message = SubFactory(MessageFactory)
    status = "read"
    status_updated_at = datetime.now() - timedelta(minutes=10)
