from django.contrib import admin

from .models import (
    Appointment,
    Participant,
    ParticipantAddress,
    ParticipantReportedMammogram,
    ScreeningEpisode,
    Symptom,
    SymptomSubType,
    SymptomType,
)


class AddressInline(admin.TabularInline):
    model = ParticipantAddress


class ParticipantReportedMammogramInline(admin.StackedInline):
    model = ParticipantReportedMammogram
    extra = 1


class SymptomInline(admin.StackedInline):
    model = Symptom
    extra = 0


class SymptomTypeAdmin(admin.ModelAdmin):
    readonly_fields = ["id"]
    list_display = ["name"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SymptomSubTypeAdmin(admin.ModelAdmin):
    readonly_fields = ["id"]
    list_display = ["symptom_type__name", "name"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ParticipantAdmin(admin.ModelAdmin):
    inlines = [AddressInline, ParticipantReportedMammogramInline]

    list_display = ["full_name"]


class AppointmentAdmin(admin.ModelAdmin):
    inlines = [SymptomInline]

    list_display = [
        "name",
        "clinic_slot__starts_at",
        "clinic_slot__duration_in_minutes",
        "current_status_display",
    ]

    readonly_fields = ["current_status_display"]

    def current_status_display(self, obj):
        return obj.current_status.state

    current_status_display.short_description = "Current Status"

    @admin.display()
    def name(self, obj):
        return obj.screening_episode.participant.full_name


class ScreeningEpisodeAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "protocol"]

    @admin.display()
    def name(self, obj):
        return obj.participant.full_name


admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(ScreeningEpisode, ScreeningEpisodeAdmin)
admin.site.register(SymptomType, SymptomTypeAdmin)
admin.site.register(SymptomSubType, SymptomSubTypeAdmin)
