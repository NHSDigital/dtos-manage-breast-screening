import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import DeleteView, FormView
from django.views.generic.detail import SingleObjectMixin

from ..services.auditor import Auditor

logger = logging.getLogger(__name__)


class NamedThingMixin:
    """
    A helper to generate consistent messages and titles.
    If needed, individual messages can be overriden in subclasses.
    """

    thing_name = None

    def add_title(self, thing_name):
        return f"Add {thing_name}"

    def added_message(self, thing_name):
        return f"Added {thing_name}"

    def update_title(self, thing_name):
        return f"Edit {thing_name}"

    def updated_message(self, thing_name):
        return f"Updated {thing_name}"

    def delete_button_text(self, thing_name):
        return f"Delete {thing_name}"

    def deleted_message_text(self, thing_name):
        return f"Deleted {thing_name}"

    def confirm_delete_link_text(self, thing_name):
        return f"Delete this {thing_name}"

    def get_thing_name(self, instance=None):
        """
        The name of the thing in lowercase, e.g. "appointment"
        """
        if self.thing_name:
            return self.thing_name

        raise ValueError("thing_name is unset")


class AddWithAuditView(NamedThingMixin, FormView):
    """
    A generic view that adds an object, similar to django.views.generic.CreateView but not based on ModelForms.
    An audit record is created and a success message is shown on redirect.

    If valid, the form's create() method will be called.
    """

    template_name = "layout-form.jinja"

    def get_success_message_content(self, object):
        return self.added_message(thing_name=self.get_thing_name(object))

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        title = self.add_title(thing_name=self.get_thing_name())

        context.update(
            {
                "heading": title,
                "page_title": title,
            },
        )

        return context

    def get_create_kwargs(self):
        return {}

    def form_valid(self, form):
        created_object = form.create(**self.get_create_kwargs())

        auditor = Auditor.from_request(self.request)
        auditor.audit_create(created_object)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message_content(created_object),
        )

        return super().form_valid(form)


class UpdateWithAuditView(NamedThingMixin, SingleObjectMixin, FormView):
    """
    A generic view that updates an object, similar to django.views.generic.UpdateView but not based on ModelForms.
    An audit record is created and a success message is shown on redirect.

    The form's constructor is expected to have an `instance` parameter.
    If valid, the form's update() method will be called.
    """

    template_name = "layout-form.jinja"

    def get_success_message_content(self, object):
        return self.updated_message(thing_name=self.get_thing_name(object))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            logger.warning("Object does not exist, redirecting to success URL")
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            raise Http404
        return super().post(request, *args, **kwargs)

    def get_delete_url(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        thing_name = self.get_thing_name(self.object)
        title = self.update_title(thing_name=thing_name)

        delete_href = self.get_delete_url()
        if delete_href:
            context["delete_link"] = {
                "text": self.confirm_delete_link_text(thing_name=thing_name),
                "class": "nhsuk-link app-link--warning",
                "href": delete_href,
            }

        context.update(
            {
                "heading": title,
                "page_title": title,
            },
        )

        return context

    def form_valid(self, form):
        created_object = form.update()

        auditor = Auditor.from_request(self.request)
        auditor.audit_update(created_object)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message_content(created_object),
        )

        return super().form_valid(form)


class DeleteWithAuditView(NamedThingMixin, DeleteView):
    """
    A generic delete view with a confirmation page, success message,
    and some default context variables.

    The object is hard deleted but the record is audited first.
    """

    template_name = "layout-confirmation.jinja"
    title_pattern = "Are you sure you want to delete this {thing_name}"

    def get_success_message_content(self, object):
        return self.deleted_message_text(thing_name=self.get_thing_name(object))

    def get_cancel_url(self):
        return self.get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thing_name = self.get_thing_name(self.object)
        title = self.title_pattern.format(thing_name=thing_name)
        context.update(
            {
                "page_title": title,
                "heading": title,
                "confirm_action": {
                    "text": self.delete_button_text(thing_name=thing_name),
                    "href": self.request.get_full_path(),
                },
                "cancel_action": {"href": self.get_cancel_url()},
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        object = self.get_object()
        auditor = Auditor.from_request(request)
        auditor.audit_delete(object)
        object.delete()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message_content(object),
        )

        return redirect(self.get_success_url())
