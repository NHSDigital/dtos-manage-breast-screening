from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import ChoiceLoader, Environment, PackageLoader
from markupsafe import Markup, escape


def no_wrap(value):
    """
    Wrap a string in a span with class app-no-wrap

    >>> no_wrap('a really long string')
    Markup('<span class="nhsuk-u-nowrap">a really long string</span>')
    """
    return Markup(
        f'<span class="nhsuk-u-nowrap">{escape(value)}</span>' if value else ""
    )


def nl2br(value):
    """
    Convert newline characters to html line breaks

    >>> nl2br('foo\\nbar\\nbaz')
    Markup('foo<br>bar<br>baz')

    >>> nl2br('<script>\\n</script>')
    Markup('&lt;script&gt;<br>&lt;/script&gt;')
    """
    lines = value.splitlines()
    return Markup("<br>".join([escape(line) for line in lines]))


def as_hint(value):
    """
    Wrap a string in a span with class app-text-grey

    >>> as_hint('Not provided')
    Markup('<span class="app-text-grey">Not provided</span>')
    """
    return Markup(f'<span class="app-text-grey">{value}</span>' if value else "")


def raise_helper(msg):
    raise Exception(msg)


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
    env.filters["no_wrap"] = no_wrap
    env.filters["as_hint"] = as_hint
    env.filters["nl2br"] = nl2br
    env.globals["raise"] = raise_helper
    return env
