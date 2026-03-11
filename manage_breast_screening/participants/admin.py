from django import forms
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


class AddressForm(forms.ModelForm):
    class Meta:
        model = ParticipantAddress
        fields = "__all__"
        help_texts = {"lines": "Comma separated lines of the address"}


class AddressInline(admin.StackedInline):
    form = AddressForm
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


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = "__all__"
        help_texts = {
            "extra_needs": 'JSON array with format [{"label": "...", "details": "...}]'
        }


class ParticipantAdmin(admin.ModelAdmin):
    form = ParticipantForm
    inlines = [AddressInline, ScreeningEpisodeInline]

    list_display = ["full_name"]


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = "__all__"
        help_texts = {
            "stopped_reasons": 'JSON array of codes e.g. ["failed_idenity_check"]'
        }


class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentForm
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


class ScreeningEpisodeAdmin(admin.ModelAdmin):
    ordering = ["participant__first_name", "participant__last_name", "created_at"]


admin_site.register(Participant, ParticipantAdmin)
admin_site.register(Appointment, AppointmentAdmin)
admin_site.register(ScreeningEpisode, ScreeningEpisodeAdmin)
