from django import forms
from django.contrib import admin

from manage_breast_screening.auth.models import Role
from manage_breast_screening.clinics.models import UserAssignment
from manage_breast_screening.core.admin import admin_site

from .models import User

_ROLE_CHOICES = [(role.value, role.value) for role in Role]


class UserAssignmentForm(forms.ModelForm):
    roles = forms.TypedMultipleChoiceField(
        choices=_ROLE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = UserAssignment
        fields = "__all__"


class AssignmentInline(admin.StackedInline):
    model = UserAssignment
    form = UserAssignmentForm


class UserAdmin(admin.ModelAdmin):
    exclude = ["password"]
    inlines = [AssignmentInline]
    extra = 0
    list_display = ["first_name", "last_name", "email", "is_staff", "is_superuser"]


admin_site.register(User, UserAdmin)
