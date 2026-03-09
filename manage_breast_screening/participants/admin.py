from django.contrib import admin

from manage_breast_screening.core.admin import admin_site

from .models import (
    Appointment,
    Participant,
    ParticipantAddress,
    ParticipantReportedMammogram,
    ScreeningEpisode,
    Symptom,
)


class AddressInline(admin.StackedInline):
    model = ParticipantAddress


class ParticipantReportedMammogramInline(admin.StackedInline):
    model = ParticipantReportedMammogram
    extra = 1


class SymptomInline(admin.StackedInline):
    model = Symptom
    extra = 0


class ScreeningEpisodeInline(admin.StackedInline):
    model = ScreeningEpisode
    fields = ["protocol", "created_at"]
    readonly_fields = ["created_at"]
    extra = 0


class ParticipantAdmin(admin.ModelAdmin):
    inlines = [AddressInline, ScreeningEpisodeInline]

    list_display = ["full_name"]


class AppointmentAdmin(admin.ModelAdmin):
    inlines = [SymptomInline, ParticipantReportedMammogramInline]

    list_display = [
        "name",
        "clinic_slot__starts_at",
        "clinic_slot__duration_in_minutes",
        "current_status_display",
    ]

    readonly_fields = ["current_status_display"]

    def current_status_display(self, obj):
        return obj.current_status.name

    current_status_display.short_description = "Current Status"

    @admin.display()
    def name(self, obj):
        return obj.screening_episode.participant.full_name


admin_site.register(Participant, ParticipantAdmin)
admin_site.register(Appointment, AppointmentAdmin)
