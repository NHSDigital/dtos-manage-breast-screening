from os import environ

# Force this setting off, so that the default jinja2 loader isn't overriden
environ["USE_PRECOMPILED_TEMPLATES"] = "false"

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import engines


class Command(BaseCommand):
    help = "Precompile jinja2 templates"

    def file_from_name(self, file_name):
        return open("manage_breast_screening/data/" + file_name)

    def handle(self, *args, **kwargs):
        engine = engines["jinja2"]
        engine.env.compile_templates(settings.BASE_DIR / "jinja2_compiled.zip")
