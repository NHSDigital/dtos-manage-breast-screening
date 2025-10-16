from django.contrib.messages import INFO, SUCCESS, get_messages
from django.urls import reverse
from django.utils.html import conditional_escape as django_html_escape
from django.utils.safestring import SafeData, SafeString, mark_safe
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


def _is_safe_message(value) -> bool:
    """
    Return true if a string is marked safe for embedding in HTML

    >>> _is_safe_message("<script>alert('boo')</script>")
    False

    >>> _is_safe_message(mark_safe("<p>Hello</p>"))
    True
    """
    return isinstance(value, SafeData)


def raise_helper(msg):
    raise Exception(msg)


def message_with_heading(heading: str, html=None) -> SafeString:
    """
    Create the HTML for a notification banner presented as a heading
    followed by some extra HTML.
    """

    heading_tag = mark_safe(
        f'<h3 class="nhsuk-notification-banner__heading">{django_html_escape(heading)}</h3>'
    )
    if html:
        return heading_tag + django_html_escape(html)
    else:
        return heading_tag


def info_banner(request, disable_auto_focus=True):
    info_messages = [
        message for message in get_messages(request) if message.level == INFO
    ]
    if not info_messages:
        return None

    info_message = info_messages[0].message
    if _is_safe_message(info_message):
        return {"html": Markup(info_message), "disableAutoFocus": disable_auto_focus}
    else:
        return {"text": info_message, "disableAutoFocus": disable_auto_focus}


def success_banner(request, disable_auto_focus=True):
    success_messages = [
        message for message in get_messages(request) if message.level == SUCCESS
    ]
    if not success_messages:
        return None

    success_message = success_messages[0].message

    if _is_safe_message(success_message):
        return {
            "html": Markup(success_message),
            "type": "success",
            "disableAutoFocus": disable_auto_focus,
        }
    else:
        return {
            "text": success_message,
            "type": "success",
            "disableAutoFocus": disable_auto_focus,
        }


def _user_name_and_role_item(user):
    if user.is_authenticated:
        name_and_role_text = f"{user.last_name.upper()}, {user.first_name}"
        roles = set()
        for assignment in user.assignments.all():
            roles.update(assignment.roles)
        if roles:
            name_and_role_text += f" ({', '.join(sorted(roles))})"

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
