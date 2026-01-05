from functools import cached_property

from django.urls import reverse

from manage_breast_screening.core.utils.date_formatting import (
    format_date,
    format_relative_date,
)


class LastKnownMammogramPresenter:
    def __init__(self, last_known_mammograms, appointment_pk, current_url):
        self._last_known_mammograms = last_known_mammograms
        self.appointment_pk = appointment_pk
        self.current_url = current_url

    @cached_property
    def last_known_mammograms(self):
        result = []

        if len(self._last_known_mammograms) == 1:
            result.append(self._present_mammogram(self._last_known_mammograms[0], None))
        else:
            for item_index, mammogram in enumerate(
                self._last_known_mammograms, start=1
            ):
                result.append(self._present_mammogram(mammogram, item_index))

        return result

    def _present_mammogram(self, mammogram, item_index):
        location = (
            mammogram.provider.name
            if mammogram.provider
            else mammogram.location_details
        )
        if mammogram.provider:
            location = mammogram.provider.name
        elif (
            mammogram.location_details
            and mammogram.location_type == mammogram.LocationType.ELSEWHERE_UK
        ):
            location = f"In the UK: {mammogram.location_details}"
        elif (
            mammogram.location_details
            and mammogram.location_type == mammogram.LocationType.OUTSIDE_UK
        ):
            location = f"Outside the UK: {mammogram.location_details}"
        elif mammogram.location_type == mammogram.LocationType.PREFER_NOT_TO_SAY:
            location = "Location: prefer not to say"
        else:
            location = "Location unknown"

        if mammogram.exact_date:
            absolute = format_date(mammogram.exact_date)
            relative = format_relative_date(mammogram.exact_date)
            date = {"absolute": absolute, "relative": relative, "is_exact": True}
        elif mammogram.approx_date:
            date = {"value": f"Approximate date: {mammogram.approx_date}"}
        else:
            date = {"value": "Date unknown"}

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

        return {
            "date_added": format_relative_date(mammogram.created_at),
            "location": location,
            "date": date,
            "different_name": mammogram.different_name,
            "additional_information": mammogram.additional_information,
            "change_link": {
                "href": href,
                "text": "Change",
                "visually_hidden_text": (
                    f" mammogram item {item_index}" if item_index else " mammogram item"
                ),
            },
            "reason_for_continuing": mammogram.reason_for_continuing,
        }

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
            "text": "Add another" if self.last_known_mammograms else "Add",
            "visually_hidden_text": "mammogram",
        }
