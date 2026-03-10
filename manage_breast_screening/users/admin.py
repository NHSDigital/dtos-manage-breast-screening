from manage_breast_screening.core.admin import admin_site

from .models import User

admin_site.register(User)
