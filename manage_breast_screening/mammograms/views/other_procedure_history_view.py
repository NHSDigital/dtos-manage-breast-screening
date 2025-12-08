import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.views.generic import DeleteWithAuditView
from manage_breast_screening.participants.models.medical_history.other_procedure_history_item import (
    OtherProcedureHistoryItem,
)

from ..forms.medical_history.other_procedure_history_item_form import (
    OtherProcedureHistoryItemForm,
)
from .mixins import InProgressAppointmentMixin

logger = logging.getLogger(__name__)


class BaseOtherProcedureHistoryView(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/medical_information/medical_history/forms/other_procedure_history.jinja"

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


class AddOtherProcedureHistoryView(BaseOtherProcedureHistoryView):
    form_class = OtherProcedureHistoryItemForm

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Details of other procedure added",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Add details of other procedures",
                "page_title": "Details of the other procedure",
            },
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs


class UpdateOtherProcedureHistoryView(BaseOtherProcedureHistoryView):
    form_class = OtherProcedureHistoryItemForm

    def get_instance(self):
        try:
            return OtherProcedureHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except OtherProcedureHistoryItem.DoesNotExist:
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
        kwargs["participant"] = self.participant
        kwargs["instance"] = self.instance
        return kwargs

    def form_valid(self, form):
        form.update(request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Details of other procedure updated",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Edit details of other procedure",
                "page_title": "Details of the other procedure",
                "delete_link": {
                    "text": "Delete this item",
                    "class": "nhsuk-link app-link--warning",
                    "href": reverse(
                        "mammograms:delete_other_procedure_history_item",
                        kwargs={
                            "pk": self.kwargs["pk"],
                            "history_item_pk": self.kwargs["history_item_pk"],
                        },
                    ),
                },
            },
        )

        return context


class DeleteOtherProcedureHistoryView(DeleteWithAuditView):
    def get_thing_name(self, object):
        return "item"

    def get_success_message_content(self, object):
        return "Deleted other procedure"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.other_procedure_history_items.get(
            pk=self.kwargs["history_item_pk"]
        )

    def get_success_url(self) -> str:
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.kwargs["pk"]},
        )
