from django.db.models import TextChoices
from django.forms import Form

from manage_breast_screening.nhsuk_forms.fields.choice_fields import ChoiceField


class RecordImagesTakenForm(Form):
    class StandardImagesChoices(TextChoices):
        YES_TWO_CC_AND_TWO_MLO = "YES_TWO_CC_AND_TWO_MLO", "Yes, 2 CC and 2 MLO"
        NO_ADD_ADDITIONAL = (
            "NO_ADD_ADDITIONAL",
            "No, add other information",
        )
        NO_IMAGES_TAKEN = "NO_IMAGES_TAKEN", "No images taken"

    standard_images = ChoiceField(
        choices=StandardImagesChoices,
        required=True,
        choice_hints={
            StandardImagesChoices.NO_ADD_ADDITIONAL: "Such as too few or additional images",
            StandardImagesChoices.NO_IMAGES_TAKEN: "The appointment cannot proceed",
        },
        label="Have you taken a standard set of images?",
        error_messages={
            "required": "Select whether you have taken a standard set of images or not"
        },
    )

    def save(self, study_service):
        match self.cleaned_data["standard_images"]:
            case self.StandardImagesChoices.YES_TWO_CC_AND_TWO_MLO:
                study_service.create_with_default_series()
            case self.StandardImagesChoices.NO_IMAGES_TAKEN:
                study_service.delete_if_exists()
            case self.StandardImagesChoices.NO_ADD_ADDITIONAL:
                # Preserve existing study data.
                pass
