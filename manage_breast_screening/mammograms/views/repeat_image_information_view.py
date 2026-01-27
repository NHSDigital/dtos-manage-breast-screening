from functools import cached_property

from django.shortcuts import redirect
from django.urls import reverse

from manage_breast_screening.core.views.generic import UpdateWithAuditView
from manage_breast_screening.mammograms.forms.repeat_image_information_form import (
    RepeatImageInformationForm,
)
from manage_breast_screening.mammograms.views.mixins import InProgressAppointmentMixin
from manage_breast_screening.manual_images.models import Study


class RepeatImageInformationView(InProgressAppointmentMixin, UpdateWithAuditView):
    form_class = RepeatImageInformationForm
    template_name = "mammograms/repeat_image_information.jinja"
    thing_name = "image information"
    model = Study

    def get_object(self, queryset=None):
        """Get the Study for this appointment."""
        return Study.objects.filter(appointment=self.appointment).first()

    @cached_property
    def series_with_repeats(self):
        """Get Series with count > 1 for this Study."""
        study = self.get_object()
        if not study:
            return []
        return list(
            study.series_set.filter(count__gt=1).order_by("laterality", "view_position")
        )

    def get(self, request, *args, **kwargs):
        # If no Study exists or no Series with count > 1, redirect to success URL
        if not self.series_with_repeats:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["series_list"] = self.series_with_repeats
        return kwargs

    def get_success_url(self):
        return reverse(
            "mammograms:check_information", kwargs={"pk": self.appointment.pk}
        )

    def get_back_link_params(self):
        return {
            "href": reverse(
                "mammograms:awaiting_images",
                kwargs={"pk": self.appointment.pk},
            ),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.appointment.participant

        context.update(
            {
                "back_link_params": self.get_back_link_params(),
                "caption": participant.full_name,
                "series_with_repeats": self.series_with_repeats,
            },
        )

        return context

    def update_title(self, thing_name):
        return "Repeat image information"

    def should_add_message(self, form) -> bool:
        return False
