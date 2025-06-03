from django.contrib import admin

from .models import Appointment, Participant, ParticipantAddress, ScreeningEpisode


class AddressInline(admin.TabularInline):
    model = ParticipantAddress


class ParticipantAdmin(admin.ModelAdmin):
    inlines = [AddressInline]


class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "clinic_slot__starts_at",
        "clinic_slot__duration_in_minutes",
        "status",
    ]

    @admin.display()
    def name(self, obj):
        return obj.screening_episode.participant.full_name


admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(ScreeningEpisode)
