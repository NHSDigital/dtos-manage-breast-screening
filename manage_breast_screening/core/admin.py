from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.auth.decorators import login_not_required
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
        return redirect(reverse(settings.LOGIN_URL, query=request.GET))


admin_site = AdminSiteWithDefaultLogin()

admin_site.register(AuditLog)
