from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.mammograms.presenters.medical_information_presenter import (
    PresentedSymptom,
)
from manage_breast_screening.participants.models.symptom import Symptom

from ..forms.symptom_forms import (
    LumpForm,
    NippleChangeForm,
    SkinChangeForm,
    SwellingOrShapeChangeForm,
)
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
                "heading": f"Details of the {self.symptom_type_name.lower()}",
                "page_title": f"Details of the {self.symptom_type_name.lower()}",
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delete_link"] = {
            "text": "Delete this symptom",
            "class": "nhsuk-link app-link--warning",
            "href": reverse(
                "mammograms:delete_symptom",
                kwargs={
                    "pk": self.kwargs["pk"],
                    "symptom_pk": self.kwargs["symptom_pk"],
                },
            ),
        }
        return context


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


class AddSkinChangeView(AddSymptomView):
    """
    Add a symptom: skin change
    """

    symptom_type_name = "Skin change"
    form_class = SkinChangeForm
    template_name = "mammograms/medical_information/symptoms/skin_change.jinja"


class AddNippleChangeView(AddSymptomView):
    """
    Add a symptom: nipple change
    """

    symptom_type_name = "Nipple change"
    form_class = NippleChangeForm
    template_name = "mammograms/medical_information/symptoms/nipple_change.jinja"


class ChangeLumpView(ChangeSymptomView):
    """
    Change a symptom: lump
    """

    symptom_type_name = "lump"
    form_class = LumpForm
    template_name = "mammograms/medical_information/symptoms/simple_symptom.jinja"


class ChangeSwellingOrShapeChangeView(ChangeSymptomView):
    """
    Change a symptom: swelling or shape change
    """

    symptom_type_name = "swelling or shape change"
    form_class = SwellingOrShapeChangeForm
    template_name = "mammograms/medical_information/symptoms/simple_symptom.jinja"


class ChangeSkinChangeView(ChangeSymptomView):
    """
    Change a symtom: skin change
    """

    symptom_type_name = "Skin change"
    form_class = SkinChangeForm
    template_name = "mammograms/medical_information/symptoms/skin_change.jinja"


class ChangeNippleChangeView(ChangeSymptomView):
    """
    Change a symptom: nipple change
    """

    symptom_type_name = "Nipple change"
    form_class = NippleChangeForm
    template_name = "mammograms/medical_information/symptoms/nipple_change.jinja"


class DeleteSymptomView(View):
    def get(self, request, *args, **kwargs):
        symptom = get_object_or_404(Symptom, pk=kwargs["symptom_pk"])

        context = {
            "page_title": "Are you sure you want to delete this symptom?",
            "heading": "Are you sure you want to delete this symptom?",
            "confirm_action": {
                "text": "Delete symptom",
                "href": reverse(
                    "mammograms:delete_symptom",
                    kwargs={
                        "pk": kwargs["pk"],
                        "symptom_pk": kwargs["symptom_pk"],
                    },
                ),
            },
            "cancel_action": {
                "href": reverse(
                    "mammograms:record_medical_information",
                    kwargs={"pk": kwargs["pk"]},
                )
            },
            "summary_list_row": PresentedSymptom.from_symptom(
                symptom
            ).build_summary_list_row(include_actions=False),
        }

        return render(
            request,
            "mammograms/medical_information/symptoms/confirm_delete_lump.jinja",
            context=context,
        )

    def post(self, request, *args, **kwargs):
        symptom = get_object_or_404(Symptom, pk=kwargs["symptom_pk"])
        auditor = Auditor.from_request(request)

        auditor.audit_delete(symptom)
        symptom.delete()
        messages.add_message(self.request, messages.SUCCESS, "Symptom deleted")

        return redirect("mammograms:record_medical_information", pk=kwargs["pk"])
