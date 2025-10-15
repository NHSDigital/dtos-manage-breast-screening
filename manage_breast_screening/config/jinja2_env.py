from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import ChoiceLoader, Environment, PackageLoader

from manage_breast_screening.core.template_helpers import (
    as_hint,
    header_account_items,
    nl2br,
    no_wrap,
    raise_helper,
)


def autoescape(template_name):
    """
    This is a workaround until https://nhsd-jira.digital.nhs.uk/browse/DTOSS-9978
    is complete.
    Going forwards, we want to use Django's default behaviour for autoescape.
    """
    if template_name is None:
        return True
    elif template_name.endswith("attributes.jinja"):
        return False
    else:
        return template_name.endswith((".html", ".htm", ".xml", ".jinja"))


def environment(**options):
    # Temporarily override autoescape for templates in nhsuk-frontend-jinja
    # remove after https://nhsd-jira.digital.nhs.uk/browse/DTOSS-9978 is complete
    options["autoescape"] = autoescape

    env = Environment(**options, extensions=["jinja2.ext.do"])
    if env.loader:
        env.loader = ChoiceLoader(
            [
                env.loader,
                PackageLoader(
                    "nhsuk_frontend_jinja", package_path="templates/nhsuk/components"
                ),
                PackageLoader(
                    "nhsuk_frontend_jinja", package_path="templates/nhsuk/macros"
                ),
                PackageLoader("nhsuk_frontend_jinja"),
            ]
        )

    env.globals.update(
        {
            "STATIC_URL": settings.STATIC_URL,
            "header_account_items": header_account_items,
            "raise": raise_helper,
            "static": static,
            "url": reverse,
        }
    )

    env.filters["no_wrap"] = no_wrap
    env.filters["as_hint"] = as_hint
    env.filters["nl2br"] = nl2br

    return env
