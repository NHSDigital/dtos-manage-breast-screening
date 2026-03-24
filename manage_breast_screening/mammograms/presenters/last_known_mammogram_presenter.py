from functools import cached_property

from django.urls import reverse

from manage_breast_screening.core.utils.date_formatting import (
    format_date,
    format_relative_date,
)


class LastKnownMammogramPresenter:
    def __init__(
        self,
        user,
        reported_mammograms,
        last_confirmed_mammogram,
        appointment_pk,
        current_url,
    ):
        self._user = user
        self._reported_mammograms = reported_mammograms
        self._last_confirmed_mammogram = last_confirmed_mammogram
        self.appointment_pk = appointment_pk
        self.current_url = current_url

    @cached_property
    def last_confirmed_mammogram(self):
        if not self._last_confirmed_mammogram:
            return None

        absolute = format_date(self._last_confirmed_mammogram.exact_date)
        relative = format_relative_date(self._last_confirmed_mammogram.exact_date)
        date = {"absolute": absolute, "relative": relative}
        return {
            "location": self._last_confirmed_mammogram.location_details,
            "date": date,
        }

    @cached_property
    def reported_mammograms(self):
        if len(self._reported_mammograms) == 1:
            return [
                self._present_mammogram(mammogram, None)
                for mammogram in self._reported_mammograms
            ]
        else:
            return [
                self._present_mammogram(mammogram, index)
                for index, mammogram in enumerate(self._reported_mammograms, start=1)
            ]

    def _present_mammogram(self, mammogram, item_index):
        href = (
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": self.appointment_pk,
                    "participant_reported_mammogram_pk": mammogram.pk,
                },
            )
            + f"?return_url={self.current_url}"
        )

        if mammogram.created_by:
            attribution = ""
            if self._user is not None and self._user.pk == mammogram.created_by.pk:
                attribution = " (you)"
            created_by = f"by {mammogram.created_by.get_short_name()}{attribution}"
        else:
            created_by = None

        return {
            "label": f"Recorded {format_date(mammogram.created_at)}",
            "created_by": created_by,
            "date_added": format_relative_date(mammogram.created_at),
            "location": self._present_mammogram_location(mammogram),
            "date": self._present_mammogram_date(mammogram),
            "different_name": mammogram.different_name,
            "additional_information": mammogram.additional_information,
            "change_link": {
                "href": href,
                "text": "Change",
                "visuallyHiddenText": (
                    f"mammogram item {item_index}" if item_index else "mammogram item"
                ),
                "classes": "nhsuk-link--no-visited-state",
            },
            "reason_for_continuing": mammogram.reason_for_continuing,
        }

    def _present_mammogram_location(self, mammogram):
        if mammogram.location_type == mammogram.LocationType.SAME_PROVIDER:
            return mammogram.appointment.provider.name
        elif mammogram.location_type == mammogram.LocationType.ANOTHER_NHS_PROVIDER:
            return f"NHS BSU: {mammogram.location_details}"
        elif (
            mammogram.location_details
            and mammogram.location_type == mammogram.LocationType.ELSEWHERE_UK
        ):
            return f"In the UK: {mammogram.location_details}"
        elif (
            mammogram.location_details
            and mammogram.location_type == mammogram.LocationType.OUTSIDE_UK
        ):
            return f"Outside the UK: {mammogram.location_details}"
        elif mammogram.location_type == mammogram.LocationType.PREFER_NOT_TO_SAY:
            return "Location: prefer not to say"
        else:
            return "Location unknown"

    def _present_mammogram_date(self, mammogram):
        if mammogram.date_type == mammogram.DateType.EXACT:
            absolute = format_date(mammogram.exact_date)
            relative = format_relative_date(mammogram.exact_date)
            return {"absolute": absolute, "relative": relative, "is_exact": True}
        elif mammogram.date_type == mammogram.DateType.MORE_THAN_SIX_MONTHS:
            return {"value": f"Taken 6 months or more ago: {mammogram.approx_date}"}
        elif mammogram.date_type == mammogram.DateType.LESS_THAN_SIX_MONTHS:
            return {"value": f"Taken less than 6 months ago: {mammogram.approx_date}"}
        else:
            return {"value": "Date unknown"}

    @cached_property
    def add_link(self):
        href = (
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": self.appointment_pk},
            )
            + f"?return_url={self.current_url}"
        )
        return {
            "href": href,
            "text": "Add another" if self._reported_mammograms else "Add",
            "visuallyHiddenText": "mammogram",
        }
