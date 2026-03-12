from .models import Provider


def get_user_providers_with_roles(user):
    """
    Get providers a user is allowed to access, which have
    roles set. If the user is a superuser, get all providers.
    """
    if user.is_superuser:
        return Provider.objects.all()
    else:
        return Provider.objects.filter(
            assignments__user=user, assignments__roles__len__gt=0
        )


def get_user_providers(user):
    """
    Get providers a user is assigned to.
    If the user is a superuser, get all providers.
    """
    if user.is_superuser:
        return Provider.objects.all()
    else:
        return Provider.objects.filter(assignments__user=user)
