from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import DeleteView

from ..services.auditor import Auditor


class DeleteWithAuditView(DeleteView):
    """
    A generic delete view with a confirmation page, success message,
    and some default context variables.

    The object is hard deleted but the record is audited first.
    """

    template_name = "layout-confirmation.jinja"

    def get_thing_name(self, object):
        return object._meta.verbose_name

    def get_success_message_content(self, object):
        return f"Deleted {self.get_thing_name(object)}"

    def get_cancel_url(self):
        return self.get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thing_name = self.get_thing_name(self.object)
        context.update(
            {
                "page_title": f"Are you sure you want to delete this {thing_name}?",
                "heading": f"Are you sure you want to delete this {thing_name}?",
                "confirm_action": {
                    "text": f"Delete {thing_name}",
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
