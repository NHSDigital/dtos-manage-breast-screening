from enum import StrEnum


class Role(StrEnum):
    ADMINISTRATIVE = "Administrative"
    CLINICAL = "Clinical"


class Permission(StrEnum):
    VIEW_PARTICIPANT_DATA = "participants.view_participant_data"
    VIEW_MAMMOGRAM_APPOINTMENT = "mammograms.view_mammogram_appointment"
    DO_MAMMOGRAM_APPOINTMENT = "mammograms.do_mammogram_appointment"
    MANAGE_PROVIDER_SETTINGS = "clinics.manage_provider_settings"
