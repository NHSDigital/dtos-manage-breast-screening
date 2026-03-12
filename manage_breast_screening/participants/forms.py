import json
import logging

from django import forms

from manage_breast_screening.nhsuk_forms.fields import CharField, ChoiceField
from manage_breast_screening.participants.services import (
    convert_bss_batch_to_participants,
)

from .models import Ethnicity

logger = logging.getLogger(__name__)


class EthnicityForm(forms.Form):
    ethnic_background_choice = ChoiceField(
        choices=Ethnicity.ethnic_background_ids_with_display_names(),
        required=True,
        error_messages={"required": "Select an ethnic background"},
    )

    def __init__(self, *args, **kwargs):
        if "participant" not in kwargs:
            raise ValueError("EthnicityForm requires a participant")
        self.participant = kwargs.pop("participant")
        super().__init__(*args, **kwargs)

        # Setup details fields for non-specific ethnicities
        for ethnic_background_id in self.non_specific_ethnic_backgrounds():
            self.fields[ethnic_background_id + "_details"] = CharField(
                required=False,
                label="How do they describe their background? (optional)",
            )

        # Set initial values
        participant_ethnic_background_id = self.participant.ethnic_background_id
        self.initial["ethnic_background_choice"] = participant_ethnic_background_id
        if participant_ethnic_background_id in self.non_specific_ethnic_backgrounds():
            self.initial[participant_ethnic_background_id + "_details"] = (
                self.participant.any_other_background_details
            )

    def ethnic_backgrounds_by_category(self):
        return Ethnicity.DATA.items()

    def non_specific_ethnic_backgrounds(self):
        return Ethnicity.non_specific_ethnic_backgrounds()

    def save(self):
        ethnic_background_id = self.cleaned_data["ethnic_background_choice"]
        self.participant.ethnic_background_id = ethnic_background_id

        if ethnic_background_id in self.non_specific_ethnic_backgrounds():
            details_field = ethnic_background_id + "_details"
            self.participant.any_other_background_details = self.cleaned_data.get(
                details_field
            )
        else:
            self.participant.any_other_background_details = ""

        self.participant.save()


class BatchForm(forms.Form):
    json_file = forms.FileField()
    description = forms.CharField(max_length=255, required=False)

    def save(self):
        logger.info("saving form")
        batch_json = json.load(self.cleaned_data["json_file"])
        convert_bss_batch_to_participants(batch_json)
