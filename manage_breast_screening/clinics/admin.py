from django.contrib import admin

from .models import Clinic, ClinicSlot, Provider, Setting


class ClinicAdmin(admin.ModelAdmin):
    readonly_fields = [
        "current_status_display",
    ]

    def current_status_display(self, obj):
        return obj.current_status.state

    current_status_display.short_description = "Current Status"


admin.site.register(Clinic, ClinicAdmin)
admin.site.register(ClinicSlot)
admin.site.register(Provider)
admin.site.register(Setting)
