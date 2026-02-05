import pytest
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.dicom.models import Image, Series, Study
from manage_breast_screening.gateway.services import (
    WorklistItemService,
    get_images_for_appointment,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestGetImagesForAppointment:
    def test_returns_empty_queryset_when_no_gateway_action(self):
        appointment = AppointmentFactory()

        images = get_images_for_appointment(appointment)

        assert not images.exists()

    def test_returns_empty_queryset_when_no_images(self):
        appointment = AppointmentFactory()
        WorklistItemService.create(appointment)

        images = get_images_for_appointment(appointment)

        assert not images.exists()

    def test_returns_images_linked_via_gateway_action(self):
        appointment = AppointmentFactory()
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
