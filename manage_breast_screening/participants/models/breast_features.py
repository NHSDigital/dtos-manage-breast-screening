import json

from django.db import models

from manage_breast_screening.core.models import BaseModel


class BreastFeatureAnnotation(BaseModel):
    class FeatureType(models.TextChoices):
        MOLE = "mole", "Mole"
        WART = "wart", "Wart"
        SCAR = "scar", "Scar"
        BRUISING_OR_TRAUMA = "bruising_or_trauma", "Bruising or trauma"
        OTHER_FEATURE = "other_feature", "Other feature"

    appointment = models.OneToOneField(
        "Appointment", on_delete=models.PROTECT, related_name="breast_features"
    )
    annotations_json = models.JSONField(null=False, default=list)
    diagram_version = models.IntegerField(null=False, default=1)

    def __str__(self):
        return json.dumps(self.annotations_json, indent=2)
