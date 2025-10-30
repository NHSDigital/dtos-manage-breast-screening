from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import ChoiceLoader, Environment, PackageLoader

from manage_breast_screening.core.template_helpers import (
    as_hint,
    get_notification_banner_params,
    header_account_items,
    nl2br,
    no_wrap,
    raise_helper,
)


def environment(**options):
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
            "get_notification_banner_params": get_notification_banner_params,
            "raise": raise_helper,
            "static": static,
            "url": reverse,
        }
    )

    env.filters["no_wrap"] = no_wrap
    env.filters["as_hint"] = as_hint
    env.filters["nl2br"] = nl2br

    return env
