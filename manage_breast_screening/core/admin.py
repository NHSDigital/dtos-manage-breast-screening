from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .models import AuditLog


class AdminSiteWithDefaultLogin(AdminSite):
    @method_decorator(require_GET)
    @method_decorator(never_cache)
    @login_not_required
    def login(self, request, extra_context=None):
        """
        Bypass Django admin's username/password login form.
        """
        if self.has_permission(request):
            # Already logged-in, redirect to admin index
            index_path = reverse("admin:index", current_app=self.name)
            return HttpResponseRedirect(index_path)
        elif request.user.is_authenticated:
            raise PermissionDenied
        else:
            return redirect(reverse(settings.LOGIN_URL, query=request.GET))


admin_site = AdminSiteWithDefaultLogin()

admin_site.register(AuditLog)
