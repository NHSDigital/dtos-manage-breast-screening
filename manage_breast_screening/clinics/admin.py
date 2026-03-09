from django.contrib import admin

from manage_breast_screening.core.admin import admin_site

from .models import Clinic, ClinicSlot, Provider, Setting


class ClinicAdmin(admin.ModelAdmin):
    readonly_fields = [
        "current_status_display",
    ]

    def current_status_display(self, obj):
        return obj.current_status.state

    current_status_display.short_description = "Current Status"


admin_site.register(Clinic, ClinicAdmin)
admin_site.register(ClinicSlot)
admin_site.register(Provider)
admin_site.register(Setting)
