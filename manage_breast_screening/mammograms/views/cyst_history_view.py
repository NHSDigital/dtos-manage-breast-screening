import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.participants.models.medical_history.cyst_history_item import (
    CystHistoryItem,
)

from ..forms.medical_history.cyst_history_item_form import CystHistoryItemForm
from .mixins import InProgressAppointmentMixin

logger = logging.getLogger(__name__)


class BaseCystHistoryView(InProgressAppointmentMixin, FormView):
    template_name = (
        "mammograms/medical_information/medical_history/forms/cyst_history.jinja"
    )

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
            },
        )

        return context


class AddCystHistoryView(BaseCystHistoryView):
    form_class = CystHistoryItemForm

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Details of cysts added",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Add details of cysts",
                "page_title": "Details of the cysts",
            },
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs


class UpdateCystHistoryView(BaseCystHistoryView):
    form_class = CystHistoryItemForm

    def get_instance(self):
        try:
            return CystHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except CystHistoryItem.DoesNotExist:
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
            "Details of cysts updated",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Edit details of cysts",
                "page_title": "Details of the cysts",
            },
        )

        return context
