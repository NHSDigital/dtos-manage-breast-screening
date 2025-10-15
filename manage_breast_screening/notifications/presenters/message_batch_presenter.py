from manage_breast_screening.notifications.models import Message, MessageBatch
from manage_breast_screening.notifications.presenters.personalisation_presenter import (
    PersonalisationPresenter,
)


class MessageBatchPresenter:
    def __init__(self, message_batch: MessageBatch):
        self.message_batch = message_batch
        self.messages = message_batch.messages.all()

    def present(self):
        return {
            "data": {
                "type": "MessageBatch",
                "attributes": {
                    "routingPlanId": str(self.message_batch.routing_plan_id),
                    "messageBatchReference": str(self.message_batch.id),
                    "messages": [self.present_message(m) for m in self.messages],
                },
            }
        }

    def present_message(self, message: Message):
        return {
            "messageReference": str(message.id),
            "recipient": {"nhsNumber": str(message.appointment.nhs_number)},
            "personalisation": PersonalisationPresenter(message.appointment).present(),
        }
