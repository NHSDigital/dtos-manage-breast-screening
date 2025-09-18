from django.urls import reverse
from markupsafe import Markup, escape


def no_wrap(value: str) -> Markup:
    """
    Wrap a string in a span with class app-no-wrap

    >>> no_wrap('a really long string')
    Markup('<span class="nhsuk-u-nowrap">a really long string</span>')
    """
    return Markup(
        f'<span class="nhsuk-u-nowrap">{escape(value)}</span>' if value else ""
    )


def nl2br(value: str) -> Markup:
    """
    Convert newline characters to html line breaks

    >>> nl2br('foo\\nbar\\nbaz')
    Markup('foo<br>bar<br>baz')

    >>> nl2br('<script>\\n</script>')
    Markup('&lt;script&gt;<br>&lt;/script&gt;')
    """
    lines = value.splitlines()
    return Markup("<br>".join([escape(line) for line in lines]))


def multiline_content(lines: list[str]) -> Markup:
    """
    Convert a list of strings to html line breaks

    >>> multiline_content(["first", "second", "third"])
    Markup('first<br>second<br>third')
    """
    return nl2br("\n".join(lines))


def as_hint(value: str) -> Markup:
    """
    Wrap a string in a span with class nhsuk-u-secondary-text-color

    >>> as_hint('Not provided')
    Markup('<span class=nhsuk-u-secondary-text-color">Not provided</span>')
    """
    return Markup(
        f'<span class=nhsuk-u-secondary-text-color">{value}</span>' if value else ""
    )


def raise_helper(msg):
    raise Exception(msg)


def _user_name_and_role_item(user):
    if user.is_authenticated:
        name_and_role_text = f"{user.last_name.upper()}, {user.first_name}"
        roles = list(user.groups.all())
        if roles:
            name_and_role_text += f" ({', '.join(role.name for role in roles)})"

        return {"text": name_and_role_text, "icon": True}


def header_account_items(user):
    items = []

    user_name_and_role = _user_name_and_role_item(user)
    if user_name_and_role:
        items.append(user_name_and_role)

    items.append(
        {
            "href": (
                reverse("auth:logout")
                if user.is_authenticated
                else reverse("auth:login")
            ),
            "text": "Log out" if user.is_authenticated else "Log in",
        }
    )

    return items
