from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.mammograms.forms.benign_lump_history_item_form import (
    BenignLumpHistoryItemForm,
)
from manage_breast_screening.participants.models.benign_lump_history_item import (
    BenignLumpHistoryItem,
)

from .mixins import InProgressAppointmentMixin


class BaseBenignLumpHistoryItemView(InProgressAppointmentMixin, FormView):
    form_class = BenignLumpHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/benign_lump_history_item_form.jinja"

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
                "participant_first_name": participant.first_name,
            },
        )

        return context


class AddBenignLumpHistoryItemView(BaseBenignLumpHistoryItemView):
    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Benign lumps added",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Add details of benign lumps",
                "page_title": "Add details of benign lumps",
            },
        )
        return context


class UpdateBenignLumpHistoryItemView(BaseBenignLumpHistoryItemView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        try:
            instance = BenignLumpHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except BenignLumpHistoryItem.DoesNotExist:
            raise Http404("Benign lump history item not found")
        kwargs["instance"] = instance

        return kwargs

    def form_valid(self, form):
        form.update(request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Benign lumps updated",
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Change details of benign lumps",
                "page_title": "Change details of benign lumps",
            },
        )
        return context
