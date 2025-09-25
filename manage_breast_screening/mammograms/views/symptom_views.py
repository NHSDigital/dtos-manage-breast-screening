from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.participants.models.symptom import Symptom

from ..forms.symptom_forms import LumpForm, SwellingOrShapeChangeForm
from .mixins import InProgressAppointmentMixin


class BaseSymptomFormView(InProgressAppointmentMixin, FormView):
    """
    Base class for views that add or change symptoms
    """

    symptom_type_name = "symptom"

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
                "heading": f"Details of the {self.symptom_type_name}",
            },
        )

        return context


class AddSymptomView(BaseSymptomFormView):
    """
    Base class for views that add symptoms
    """

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        return super().form_valid(form)


class ChangeSymptomView(BaseSymptomFormView):
    """
    Base class for views that change symptoms
    """

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        instance = get_object_or_404(
            Symptom, pk=self.kwargs["symptom_pk"], appointment_id=self.kwargs["pk"]
        )
        kwargs["instance"] = instance

        return kwargs

    def form_valid(self, form):
        form.update(request=self.request)

        return super().form_valid(form)


class AddLumpView(AddSymptomView):
    """
    Add a symptom: lump
    """

    symptom_type_name = "lump"
    form_class = LumpForm
    template_name = "mammograms/medical_information/symptoms/simple_symptom.jinja"


class AddSwellingOrShapeChangeView(AddSymptomView):
    """
    Add a symptom: swelling or shape change
    """

    symptom_type_name = "swelling or shape change"
    form_class = SwellingOrShapeChangeForm
    template_name = "mammograms/medical_information/symptoms/simple_symptom.jinja"


class ChangeLumpView(ChangeSymptomView):
    """
    Change a symptom: lump
    """

    symptom_type_name = "lump"
    form_class = LumpForm
    template_name = "mammograms/medical_information/symptoms/simple_symptom.jinja"


class ChangeSwellingOrShapeChangeView(ChangeSymptomView):
    """
    Change a symptom: lump
    """

    symptom_type_name = "swelling or shape change"
    form_class = SwellingOrShapeChangeForm
    template_name = "mammograms/medical_information/symptoms/simple_symptom.jinja"
