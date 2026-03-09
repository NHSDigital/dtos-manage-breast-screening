from django.contrib import admin

from manage_breast_screening.clinics.models import UserAssignment
from manage_breast_screening.core.admin import admin_site

from .models import User


class AssignmentInline(admin.StackedInline):
    model = UserAssignment


class UserAdmin(admin.ModelAdmin):
    exclude = ["password"]
    inlines = [AssignmentInline]
    extra = 0


admin_site.register(User, UserAdmin)
