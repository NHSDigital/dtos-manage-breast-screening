import logging
from typing import Any

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.views.generic import DeleteWithAuditView
from manage_breast_screening.mammograms.forms.breast_cancer_history_form import (
    BreastCancerHistoryForm,
    BreastCancerHistoryUpdateForm,
)
from manage_breast_screening.participants.models.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)

from .mixins import InProgressAppointmentMixin

logger = logging.getLogger(__name__)


class BaseBreastCancerHistoryView(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/medical_information/medical_history/forms/breast_cancer_history_item_form.jinja"

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
            "text": "Back",
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


class AddBreastCancerHistoryView(BaseBreastCancerHistoryView):
    form_class = BreastCancerHistoryForm

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Breast cancer history added",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Add details of breast cancer",
                "page_title": "Add details of breast cancer",
            },
        )

        return context


class ChangeBreastCancerHistoryView(BaseBreastCancerHistoryView):
    form_class = BreastCancerHistoryUpdateForm

    def get_instance(self):
        try:
            return self.appointment.breast_cancer_history_items.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except BreastCancerHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None

    def get(self, request, *args, **kwargs):
        self.instance = self.get_instance()
        if self.instance is None:
            # For a GET request, if the page shouldn't exist we can
            # safely redirect to the hub page.
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.instance = self.get_instance()
        if self.instance is None:
            raise Http404
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.instance
        return kwargs

    def form_valid(self, form):
        form.update(request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Breast cancer history updated",
        )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "heading": "Edit details of breast cancer",
                "page_title": "Edit details of breast cancer",
                "delete_link": {
                    "text": "Delete this item",
                    "class": "nhsuk-link app-link--warning",
                    "href": reverse(
                        "mammograms:delete_breast_cancer_history_item",
                        kwargs={
                            "pk": self.kwargs["pk"],
                            "history_item_pk": self.kwargs["history_item_pk"],
                        },
                    ),
                },
            },
        )

        return context


class DeleteBreastCancerHistoryView(DeleteWithAuditView):
    def get_thing_name(self, object):
        return "item"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.breast_cancer_history_items.get(
            pk=self.kwargs["history_item_pk"]
        )

    def get_success_url(self) -> str:
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.kwargs["pk"]},
        )
