from django.contrib import admin

from .models import (
    Appointment,
    Participant,
    ParticipantAddress,
    ParticipantReportedMammogram,
    ScreeningEpisode,
)


class AddressInline(admin.TabularInline):
    model = ParticipantAddress


class ParticipantReportedMammogramInline(admin.StackedInline):
    model = ParticipantReportedMammogram
    extra = 1


class ParticipantAdmin(admin.ModelAdmin):
    inlines = [AddressInline, ParticipantReportedMammogramInline]

    list_display = ["full_name"]


class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "clinic_slot__starts_at",
        "clinic_slot__duration_in_minutes",
        "statuses__state",
    ]

    @admin.display()
    def name(self, obj):
        return obj.screening_episode.participant.full_name


admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(ScreeningEpisode)
