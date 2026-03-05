from django import forms

from .models import ProviderConfig


class UpdateProviderSettingsForm(forms.ModelForm):
    class Meta:
        model = ProviderConfig
        fields = ["manual_image_collection"]
