import re

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import ChoiceLoader, Environment, PackageLoader
from markupsafe import Markup, escape

from ..utils.date_formatting import (
    format_date,
    format_date_time,
    format_relative_date,
    format_time,
    format_time_range,
)


def no_wrap(value):
    """
    Wrap a string in a span with class app-no-wrap

    >>> no_wrap('a really long string')
    Markup('<span class="nhsuk-u-nowrap">a really long string</span>')
    """
    return Markup(
        f'<span class="nhsuk-u-nowrap">{escape(value)}</span>' if value else ""
    )


def as_hint(value):
    """
    Wrap a string in a span with class app-text-grey

    >>> as_hint('Not provided')
    Markup('<span class="app-text-grey">Not provided</span>')
    """
    return Markup(f'<span class="app-text-grey">{value}</span>' if value else "")


def environment(**options):
    env = Environment(**options, extensions=["jinja2.ext.do"])
    if env.loader:
        env.loader = ChoiceLoader(
            [
                env.loader,
                PackageLoader(
                    "nhsuk_frontend_jinja", package_path="templates/components"
                ),
                PackageLoader("nhsuk_frontend_jinja", package_path="templates/macros"),
                PackageLoader("nhsuk_frontend_jinja"),
            ]
        )

    env.globals.update(
        {"static": static, "url": reverse, "STATIC_URL": settings.STATIC_URL}
    )
    env.filters["as_hint"] = as_hint

    # TODO: format all dates and times in the presenter layer
    env.filters["format_date"] = format_date
    env.filters["format_time_range"] = format_time_range

    return env
