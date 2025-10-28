import json
import os
from datetime import datetime

import pytest
from jsonschema import ValidationError, validate

from manage_breast_screening.notifications.models import ZONE_INFO
from manage_breast_screening.notifications.presenters.message_batch_presenter import (
    MessageBatchPresenter,
)
from manage_breast_screening.notifications.presenters.personalisation_presenter import (
    PersonalisationPresenter,
)
from manage_breast_screening.notifications.tests.factories import (
    AppointmentFactory,
    ClinicFactory,
    MessageBatchFactory,
    MessageFactory,
)


@pytest.mark.django_db
class TestMessageBatchPresenter:
    def test_present(self):
        appointment1 = AppointmentFactory(
            starts_at=datetime(2025, 9, 9, 9, 30, tzinfo=ZONE_INFO),
            clinic=ClinicFactory(
                code="MDSSH",
                bso_code="MBD",
                address_line_1="Birmingham Treatment Centre",
                address_line_2="Floor 1",
                address_line_3="City Health Campus",
                address_line_4="Dudley Road",
                address_line_5="West Midlands",
                postcode="B71 4HJ",
            ),
        )
        appointment2 = AppointmentFactory(
            starts_at=datetime(2025, 11, 12, 9, 45, tzinfo=ZONE_INFO),
            clinic=ClinicFactory(
                code="MDSVH",
                bso_code="MBD",
                address_line_1="Victoria Health Centre",
                address_line_2="5 Suffrage Street",
                address_line_3="Off Windmill Lane",
                address_line_4="Smethwick",
                address_line_5="",
                postcode="B66 3PZ",
            ),
        )
        message1 = MessageFactory(appointment=appointment1)
        message2 = MessageFactory(appointment=appointment2)
        message_batch = MessageBatchFactory(messages=[message1, message2])

        subject = MessageBatchPresenter(message_batch).present()

        assert subject["data"]["type"] == "MessageBatch"
        attributes = subject["data"]["attributes"]
        assert attributes["routingPlanId"] == str(message_batch.routing_plan_id)
        assert attributes["messageBatchReference"] == str(message_batch.id)

        first_message = attributes["messages"][0]
        assert first_message["messageReference"] == str(message1.id)
        assert first_message["recipient"]["nhsNumber"] == str(appointment1.nhs_number)
        assert (
            first_message["personalisation"]
            == PersonalisationPresenter(appointment1).present()
        )

        second_message = attributes["messages"][1]
        assert second_message["messageReference"] == str(message2.id)
        assert second_message["recipient"]["nhsNumber"] == str(appointment2.nhs_number)
        assert (
            second_message["personalisation"]
            == PersonalisationPresenter(appointment2).present()
        )

    def test_present_is_valid_for_notify_schema(self):
        appointment = AppointmentFactory(
            starts_at=datetime(2025, 9, 9, 9, 30, tzinfo=ZONE_INFO),
            clinic=ClinicFactory(
                code="MDSSH",
                bso_code="MBD",
                address_line_1="Birmingham Treatment Centre",
                address_line_2="Floor 1",
                address_line_3="City Health Campus",
                address_line_4="Dudley Road",
                postcode="B71 4HJ",
            ),
        )
        message_batch = MessageBatchFactory(
            messages=[MessageFactory(appointment=appointment)]
        )
        path = (
            os.path.dirname(os.path.realpath(__file__))
            + "/../dependencies/notify_api_stub/schema.json"
        )
        with open(path) as file:
            schema = json.loads(file.read())
            subschema = schema["paths"]["/v1/message-batches"]["post"]["requestBody"][
                "content"
            ]["application/vnd.api+json"]["schema"]

        try:
            validate(
                instance=MessageBatchPresenter(message_batch).present(),
                schema=subschema,
            )
            assert True
        except ValidationError:
            self.fail(
                "MessageBatchPresenter#present() does not conform to Notify schema"
            )
