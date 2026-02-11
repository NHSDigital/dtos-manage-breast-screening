from unittest.mock import patch

import pytest
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.dicom.models import Image, Series, Study
from manage_breast_screening.gateway.relay_service import RelayService
from manage_breast_screening.gateway.tests.factories import RelayFactory
from manage_breast_screening.gateway.worklist_item_service import (
    WorklistItemService,
    get_images_for_appointment,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@patch.object(RelayService, "send_action")
@pytest.mark.django_db
class TestGetImagesForAppointment:
    def test_returns_empty_queryset_when_no_gateway_action(self, _):
        appointment = AppointmentFactory()
        RelayFactory(provider=appointment.provider)

        images = get_images_for_appointment(appointment)

        assert not images.exists()

    def test_returns_empty_queryset_when_no_images(self, _):
        appointment = AppointmentFactory()
        RelayFactory(provider=appointment.provider)

        WorklistItemService.create(appointment)

        images = get_images_for_appointment(appointment)

        assert not images.exists()

    def test_returns_images_linked_via_gateway_action(self, _):
        appointment = AppointmentFactory()
        RelayFactory(provider=appointment.provider)

        action = WorklistItemService.create(appointment)

        study = Study.objects.create(
            study_instance_uid="1.2.826.0.1.1",  # gitleaks:allow
            source_message_id=str(action.id),
        )
        series = Series.objects.create(
            study=study,
            series_instance_uid="1.2.826.0.1.2",  # gitleaks:allow
        )
        image = Image.objects.create(
            series=series,
            sop_instance_uid="1.2.826.0.1.3",  # gitleaks:allow
        )

        images = get_images_for_appointment(appointment)

        assertQuerySetEqual(images, [image])
