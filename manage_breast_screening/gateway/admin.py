from django.contrib import admin

from manage_breast_screening.core.admin import admin_site

from .models import Relay


@admin.register(Relay, site=admin_site)
class RelayAdmin(admin.ModelAdmin):
    list_display = ["setting", "namespace", "hybrid_connection_name"]
    list_select_related = ["setting"]
