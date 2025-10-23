from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.mammograms.presenters.symptom_presenter import (
    SymptomPresenter,
)
from manage_breast_screening.participants.models.symptom import Symptom, SymptomType

from ..forms.symptom_forms import (
    LumpForm,
    NippleChangeForm,
    OtherSymptomForm,
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
        symptom = form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            SymptomPresenter(symptom).add_message_html,
        )

        return super().form_valid(form)


class ChangeSymptomView(BaseSymptomFormView):
    """
    Base class for views that change symptoms
    """

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        try:
            instance = Symptom.objects.get(
                pk=self.kwargs["symptom_pk"],
                appointment_id=self.kwargs["pk"],
                **self.extra_filters(),
            )
        except Symptom.DoesNotExist:
            raise Http404("Symptom not found")
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

    def extra_filters(self):
        """
        Override this method to filter objects editable by this form
        """
        raise NotImplementedError


class AddLumpView(AddSymptomView):
    """
    Add a symptom: lump
    """

    symptom_type_name = "lump"
    form_class = LumpForm
    template_name = "mammograms/medical_information/symptoms/forms/simple_symptom.jinja"


class AddSwellingOrShapeChangeView(AddSymptomView):
    """
    Add a symptom: swelling or shape change
    """

    symptom_type_name = "swelling or shape change"
    form_class = SwellingOrShapeChangeForm
    template_name = "mammograms/medical_information/symptoms/forms/simple_symptom.jinja"


class AddSkinChangeView(AddSymptomView):
    """
    Add a symptom: skin change
    """

    symptom_type_name = "Skin change"
    form_class = SkinChangeForm
    template_name = "mammograms/medical_information/symptoms/forms/skin_change.jinja"


class AddNippleChangeView(AddSymptomView):
    """
    Add a symptom: nipple change
    """

    symptom_type_name = "Nipple change"
    form_class = NippleChangeForm
    template_name = "mammograms/medical_information/symptoms/forms/nipple_change.jinja"


class AddOtherSymptomView(AddSymptomView):
    """
    Add a symptom: other
    """

    symptom_type_name = "Other"
    form_class = OtherSymptomForm
    template_name = "mammograms/medical_information/symptoms/forms/other.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["heading"] = "Symptom details"
        return context


class ChangeLumpView(ChangeSymptomView):
    """
    Change a symptom: lump
    """

    symptom_type_name = "lump"
    form_class = LumpForm
    template_name = "mammograms/medical_information/symptoms/forms/simple_symptom.jinja"

    def extra_filters(self):
        return {"symptom_type_id": SymptomType.LUMP}


class ChangeSwellingOrShapeChangeView(ChangeSymptomView):
    """
    Change a symptom: swelling or shape change
    """

    symptom_type_name = "swelling or shape change"
    form_class = SwellingOrShapeChangeForm
    template_name = "mammograms/medical_information/symptoms/forms/simple_symptom.jinja"

    def extra_filters(self):
        return {"symptom_type_id": SymptomType.SWELLING_OR_SHAPE_CHANGE}


class ChangeSkinChangeView(ChangeSymptomView):
    """
    Change a symtom: skin change
    """

    symptom_type_name = "Skin change"
    form_class = SkinChangeForm
    template_name = "mammograms/medical_information/symptoms/forms/skin_change.jinja"

    def extra_filters(self):
        return {"symptom_type_id": SymptomType.SKIN_CHANGE}


class ChangeNippleChangeView(ChangeSymptomView):
    """
    Change a symptom: nipple change
    """

    symptom_type_name = "Nipple change"
    form_class = NippleChangeForm
    template_name = "mammograms/medical_information/symptoms/forms/nipple_change.jinja"

    def extra_filters(self):
        return {"symptom_type_id": SymptomType.NIPPLE_CHANGE}


class ChangeOtherSymptomView(ChangeSymptomView):
    """
    Change a symptom: other
    """

    symptom_type_name = "Other"
    form_class = OtherSymptomForm
    template_name = "mammograms/medical_information/symptoms/forms/other.jinja"

    def extra_filters(self):
        return {"symptom_type_id": SymptomType.OTHER}

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["heading"] = "Symptom details"
        return context


class DeleteSymptomView(View):
    def get(self, request, *args, **kwargs):
        try:
            symptom = Symptom.objects.get(pk=kwargs["symptom_pk"])
        except Symptom.DoesNotExist:
            raise Http404("Symptom not found")

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
            "summary_list_row": SymptomPresenter(symptom).build_summary_list_row(
                include_actions=False
            ),
        }

        return render(
            request,
            "mammograms/medical_information/symptoms/confirm_delete_lump.jinja",
            context=context,
        )

    def post(self, request, *args, **kwargs):
        try:
            symptom = Symptom.objects.get(pk=kwargs["symptom_pk"])
        except Symptom.DoesNotExist:
            raise Http404("Symptom not found")
        auditor = Auditor.from_request(request)

        presenter = SymptomPresenter(symptom)

        auditor.audit_delete(symptom)
        symptom.delete()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            presenter.delete_message_html,
        )

        return redirect("mammograms:record_medical_information", pk=kwargs["pk"])
