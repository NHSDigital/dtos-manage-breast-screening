import uuid
from datetime import datetime, timedelta

from factory import Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory

from .. import models


class ClinicFactory(DjangoModelFactory):
    class Meta:
        model = models.Clinic

    code = "BU001"
    name = "BREAST CARE UNIT"
    holding_clinic = False


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = models.Appointment

    clinic = SubFactory(ClinicFactory)
    nhs_number = Sequence(lambda n: int("999%06d" % n))
    starts_at = datetime.now() + timedelta(weeks=4, days=4)


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = models.Message

    appointment = SubFactory(AppointmentFactory)


class MessageBatchFactory(DjangoModelFactory):
    class Meta:
        model = models.MessageBatch

    routing_plan_id = str(uuid.uuid4())
    status = "unscheduled"

    @post_generation
    def messages(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for message in extracted:
                self.messages.add(message)
