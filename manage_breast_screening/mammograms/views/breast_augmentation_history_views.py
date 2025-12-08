import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)

from ..forms.medical_history.breast_augmentation_history_item_form import (
    BreastAugmentationHistoryItemForm,
)
from .mixins import InProgressAppointmentMixin

logger = logging.getLogger(__name__)


class BreastAugmentationHistoryBaseView(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/medical_information/medical_history/forms/breast_augmentation_history.jinja"

    def get_success_url(self):
        return reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )

    def get_back_link_params(self):
        return {
            "href": reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment_pk},
            ),
            "text": "Back to appointment",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        participant = self.appointment.participant

        context.update(
            {
                "back_link_params": self.get_back_link_params(),
                "caption": participant.full_name,
                "participant_first_name": participant.first_name,
            },
        )

        return context


class AddBreastAugmentationHistoryView(BreastAugmentationHistoryBaseView):
    form_class = BreastAugmentationHistoryItemForm

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Details of breast implants or augmentation added",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Add details of breast implants or augmentation",
                "page_title": "Add details of breast implants or augmentation",
            },
        )

        return context


class UpdateBreastAugmentationHistoryView(BreastAugmentationHistoryBaseView):
    form_class = BreastAugmentationHistoryItemForm

    def get_instance(self):
        try:
            return BreastAugmentationHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except BreastAugmentationHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None

    def get(self, *args, **kwargs):
        self.instance = self.get_instance()
        if not self.instance:
            # For a GET request, if the page shouldn't exist we can
            # safely redirect to the hub page.
            return redirect(self.get_success_url())
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.instance = self.get_instance()
        if not self.instance:
            raise Http404
        return super().post(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.instance
        return kwargs

    def form_valid(self, form):
        form.update(request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Details of breast implants or augmentation updated",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Edit details of breast implants or augmentation",
                "page_title": "Edit details of breast implants or augmentation",
            },
        )

        return context
