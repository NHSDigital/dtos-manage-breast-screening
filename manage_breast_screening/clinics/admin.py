from django.contrib import admin

from manage_breast_screening.core.admin import admin_site

from .models import Clinic, ClinicSlot, Provider, Setting


class ClinicSlotInline(admin.StackedInline):
    model = ClinicSlot
    extra = 5


class SettingInline(admin.StackedInline):
    model = Setting
    extra = 1


class ClinicAdmin(admin.ModelAdmin):
    inlines = [ClinicSlotInline]
    readonly_fields = [
        "current_status_display",
    ]

    def current_status_display(self, obj):
        return obj.current_status.state

    current_status_display.short_description = "Current Status"


class ProviderAdmin(admin.ModelAdmin):
    inlines = [SettingInline]


admin_site.register(Clinic, ClinicAdmin)
admin_site.register(Provider, ProviderAdmin)
