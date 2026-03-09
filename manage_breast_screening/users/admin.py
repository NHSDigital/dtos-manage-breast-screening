from django.contrib import admin

from manage_breast_screening.core.admin import admin_site

from .models import User


class UserAdmin(admin.ModelAdmin):
    exclude = ["password"]


admin_site.register(User, UserAdmin)
