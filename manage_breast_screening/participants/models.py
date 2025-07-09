import uuid
from datetime import date
from logging import getLogger

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import OuterRef, Subquery

from ..clinics.models import Provider
from ..core.models import BaseModel

logger = getLogger(__name__)


class Ethnicity:
    """
    This class contains structured ethnicity data along with methods for retrieval and querying of
    the dataset.

    List of ethnic groups from
    https://design-system.service.gov.uk/patterns/equality-information/
    This list is specific to England.

    The ids are stored in the database and should not be changed without an accompanying data
    migration.
    """

    # fmt: off
    DATA = {
        "White": [
            { "id": "english_welsh_scottish_ni_british", "display_name": "English, Welsh, Scottish, Northern Irish or British", },
            { "id": "irish", "display_name": "Irish" },
            { "id": "gypsy_or_irish_traveller", "display_name": "Gypsy or Irish Traveller" },
            { "id": "any_other_white_background", "display_name": "Any other White background" },
        ],
        "Mixed or multiple ethnic groups": [
            { "id": "white_and_black_caribbean", "display_name": "White and Black Caribbean" },
            { "id": "white_and_black_african", "display_name": "White and Black African" },
            { "id": "white_and_asian", "display_name": "White and Asian" },
            { "id": "any_other_mixed_or_multiple_ethnic_background", "display_name": "Any other mixed or multiple ethnic background" },
        ],
        "Asian or Asian British": [
            { "id": "indian", "display_name": "Indian" },
            { "id": "pakistani", "display_name": "Pakistani" },
            { "id": "bangladeshi", "display_name": "Bangladeshi" },
            { "id": "chinese", "display_name": "Chinese" },
            { "id": "any_other_asian_background", "display_name": "Any other Asian background" },
        ],
        "Black, African, Caribbean or Black British": [
            { "id": "african", "display_name": "African" },
            { "id": "caribbean", "display_name": "Caribbean" },
            { "id": "any_other_black_african_or_caribbean_background", "display_name": "Any other Black, African or Caribbean background" },
        ],
        "Other ethnic group": [
            { "id": "arab", "display_name": "Arab" },
            { "id": "any_other_ethnic_background", "display_name": "Any other ethnic group" },
            { "id": "prefer_not_to_say", "display_name": "Prefer not to say" },
        ],
    }
    # fmt: on

    @staticmethod
    def non_specific_ethnic_backgrounds():
        return [
            "any_other_white_background",
            "any_other_mixed_or_multiple_ethnic_background",
            "any_other_asian_background",
            "any_other_black_african_or_caribbean_background",
            "any_other_ethnic_background",
        ]

    @classmethod
    def ethnic_background_ids_with_display_names(cls):
        """
        Returns a list of tuples containing the id and display name for each ethnic background.
        """
        choices = []
        for ethnic_backgrounds in cls.DATA.values():
            for background in ethnic_backgrounds:
                choices.append((background["id"], background["display_name"]))
        return tuple(choices)

    @classmethod
    def ethnic_category(cls, ethnic_background_id: str):
        """
        Returns the top-level ethnic category for the given ethnic background id.
        """
        for category, ethnic_backgrounds in cls.DATA.items():
            for background in ethnic_backgrounds:
                if ethnic_background_id == background["id"]:
                    return category
        return None

    @classmethod
    def ethnic_background_display_name(cls, ethnic_background_id: str):
        """
        Returns the display name for the given ethnic background id.
        """
        for _, ethnic_backgrounds in cls.DATA.items():
            for background in ethnic_backgrounds:
                if ethnic_background_id == background["id"]:
                    return background["display_name"]
        return None


class Participant(BaseModel):
    PREFER_NOT_TO_SAY = "Prefer not to say"
    ETHNIC_BACKGROUND_CHOICES = Ethnicity.ethnic_background_ids_with_display_names()

    first_name = models.TextField()
    last_name = models.TextField()
    gender = models.TextField()
    nhs_number = models.TextField()
    phone = models.TextField()
    email = models.EmailField()
    date_of_birth = models.DateField()
    ethnic_background_id = models.CharField(
        blank=True, null=True, choices=ETHNIC_BACKGROUND_CHOICES
    )
    any_other_background_details = models.TextField(blank=True, null=True)
    risk_level = models.TextField()
    extra_needs = models.JSONField(null=False, default=list, blank=True)

    @property
    def full_name(self):
        return " ".join([name for name in [self.first_name, self.last_name] if name])

    def age(self):
        today = date.today()
        if (today.month, today.day) >= (
            self.date_of_birth.month,
            self.date_of_birth.day,
        ):
            return today.year - self.date_of_birth.year
        else:
            return today.year - self.date_of_birth.year - 1

    @property
    def ethnic_category(self):
        return Ethnicity.ethnic_category(self.ethnic_background_id)

    @property
    def ethnic_background(self):
        if (
            self.ethnic_background_id in Ethnicity.non_specific_ethnic_backgrounds()
            and self.any_other_background_details
        ):
            return self.any_other_background_details
        else:
            return Ethnicity.ethnic_background_display_name(self.ethnic_background_id)


class ParticipantAddress(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    participant = models.OneToOneField(
        Participant, on_delete=models.PROTECT, related_name="address"
    )
    lines = ArrayField(models.CharField(), size=5, blank=True)
    postcode = models.CharField(blank=True, null=True)


class ScreeningEpisode(BaseModel):
    class Protocol:
        FAMILY_HISTORY = "FAMILY_HISTORY"

    PROTOCOL_CHOICES = {
        Protocol.FAMILY_HISTORY: "Family history",
    }

    participant = models.ForeignKey(Participant, on_delete=models.PROTECT)
    protocol = models.CharField(
        choices=PROTOCOL_CHOICES, default=Protocol.FAMILY_HISTORY, max_length=50
    )

    def screening_history(self):
        """
        Return all previous screening episodes, excluding this one, prefetching
        their appointment details as well.
        """
        return (
            ScreeningEpisode.objects.prefetch_related(
                "appointment_set__clinic_slot__clinic__setting__provider"
            )
            .filter(participant__pk=self.participant.pk)
            .exclude(pk=self.pk)
            .order_by("-created_at")
        )

    def previous(self) -> "ScreeningEpisode | None":
        """
        Return the last known screening episode
        """
        try:
            return self.screening_history()[0]
        except IndexError:
            return None


class AppointmentQuerySet(models.QuerySet):
    def in_status(self, *statuses):
        return self.filter(
            statuses=Subquery(
                AppointmentStatus.objects.filter(
                    appointment=OuterRef("pk"),
                    state__in=statuses,
                )
                .values("pk")
                .order_by("-created_at")[:1]
            )
        )

    def remaining(self):
        return self.in_status(
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
        )

    def checked_in(self):
        return self.in_status(AppointmentStatus.CHECKED_IN)

    def complete(self):
        return self.in_status(
            AppointmentStatus.CANCELLED,
            AppointmentStatus.DID_NOT_ATTEND,
            AppointmentStatus.SCREENED,
            AppointmentStatus.PARTIALLY_SCREENED,
            AppointmentStatus.ATTENDED_NOT_SCREENED,
        )

    def upcoming(self):
        return self.filter(clinic_slot__starts_at__gte=date.today())

    def past(self):
        return self.filter(clinic_slot__starts_at__lt=date.today())

    def for_clinic_and_filter(self, clinic, filter):
        match filter:
            case "remaining":
                return self.remaining().filter(clinic_slot__clinic=clinic)
            case "checked_in":
                return self.checked_in().filter(clinic_slot__clinic=clinic)
            case "complete":
                return self.complete().filter(clinic_slot__clinic=clinic)
            case "all":
                return self.filter(clinic_slot__clinic=clinic)
            case _:
                raise ValueError(filter)

    def filter_counts_for_clinic(self, clinic):
        counts = {}
        for filter in ["remaining", "checked_in", "complete", "all"]:
            counts[filter] = self.for_clinic_and_filter(clinic, filter).count()
        return counts


class Appointment(BaseModel):
    objects = AppointmentQuerySet.as_manager()

    screening_episode = models.ForeignKey(ScreeningEpisode, on_delete=models.PROTECT)
    clinic_slot = models.ForeignKey(
        "clinics.ClinicSlot",
        on_delete=models.PROTECT,
    )
    reinvite = models.BooleanField(default=False)
    stopped_reasons = models.JSONField(null=True, blank=True)

    @property
    def current_status(self) -> "AppointmentStatus":
        """
        Fetch the most recent status associated with this appointment.
        If there are no statuses for any reason, assume the default one.
        """
        # avoid `first()` here so that `statuses` can be prefetched
        # when fetching many appointments
        statuses = list(self.statuses.order_by("-created_at").all())

        if not statuses:
            status = AppointmentStatus()
            logger.info(
                f"Appointment {self.pk} has no statuses. Assuming {status.state}"
            )
            return status

        return statuses[0]


class AppointmentStatus(models.Model):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DID_NOT_ATTEND = "DID_NOT_ATTEND"
    CHECKED_IN = "CHECKED_IN"
    SCREENED = "SCREENED"
    PARTIALLY_SCREENED = "PARTIALLY_SCREENED"
    ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED"

    STATUS_CHOICES = {
        CONFIRMED: "Confirmed",
        CANCELLED: "Cancelled",
        DID_NOT_ATTEND: "Did not attend",
        CHECKED_IN: "Checked in",
        SCREENED: "Screened",
        PARTIALLY_SCREENED: "Partially screened",
        ATTENDED_NOT_SCREENED: "Attended not screened",
    }
    state = models.CharField(choices=STATUS_CHOICES, max_length=50, default=CONFIRMED)

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(
        Appointment, on_delete=models.PROTECT, related_name="statuses"
    )

    class Meta:
        ordering = ["-created_at"]


class ParticipantReportedMammogram(BaseModel):
    class LocationType(models.TextChoices):
        NHS_BREAST_SCREENING_UNIT = (
            "NHS_BREAST_SCREENING_UNIT",
            "At an NHS breast screening unit",
        )
        ELSEWHERE_UK = "ELSEWHERE_UK", "Elsewhere in the UK"
        OUTSIDE_UK = "OUTSIDE_UK", "Outside the UK"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    participant = models.ForeignKey(
        Participant, on_delete=models.PROTECT, related_name="reported_mammograms"
    )
    location_type = models.CharField(choices=LocationType)
    provider = models.ForeignKey(
        Provider, on_delete=models.PROTECT, null=True, blank=True
    )
    location_details = models.TextField(null=False, default="", blank=True)
    exact_date = models.DateField(null=True, blank=True)
    approx_date = models.CharField(null=False, default="", blank=True)
    different_name = models.CharField(null=False, default="", blank=True)
    additional_information = models.TextField(null=False, default="", blank=True)
