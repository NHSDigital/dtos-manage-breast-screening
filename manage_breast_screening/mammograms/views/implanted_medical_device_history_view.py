import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)

from ..forms.medical_history.implanted_medical_device_history_item_form import (
    ImplantedMedicalDeviceHistoryItemForm,
)
from .mixins import InProgressAppointmentMixin

logger = logging.getLogger(__name__)


class BaseImplantedMedicalDeviceHistoryView(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/medical_information/medical_history/forms/implanted_medical_device_history.jinja"

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
                "heading": "Add details of implanted medical device",
                "page_title": "Details of the implanted medical device",
            },
        )

        return context


class AddImplantedMedicalDeviceHistoryView(BaseImplantedMedicalDeviceHistoryView):
    form_class = ImplantedMedicalDeviceHistoryItemForm

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Implanted medical device added",
        )

        return super().form_valid(form)

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
                "heading": "Add details of implanted medical device",
                "page_title": "Details of the implanted medical device",
            },
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs


class ChangeImplantedMedicalDeviceHistoryView(BaseImplantedMedicalDeviceHistoryView):
    form_class = ImplantedMedicalDeviceHistoryItemForm

    def get_instance(self):
        try:
            return ImplantedMedicalDeviceHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except ImplantedMedicalDeviceHistoryItem.DoesNotExist:
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
        kwargs["participant"] = self.participant
        return kwargs

    def form_valid(self, form):
        form.update(request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Details of implanted medical device updated",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Edit details of implanted medical device",
                "page_title": "Details of the implanted medical device",
            },
        )

        return context
