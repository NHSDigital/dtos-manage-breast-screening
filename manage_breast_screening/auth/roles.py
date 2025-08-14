from django.contrib.auth.models import Group, Permission

ROLES = {
    "Administrative": {
        "participants": [
            "view_participant",
            "change_participant",
            "add_participantaddress",
            "view_participantaddress",
            "change_participantaddress",
            "view_appointment",
            "change_appointment",
            "view_appointmentstatus",
            "add_appointmentstatus",
            "view_participantreportedmammogram",
            "add_participantreportedmammogram",
        ]
    },
    "Clinical": {
        "participants": [
            "view_participant",
            "change_participant",
            "add_participantaddress",
            "view_participantaddress",
            "change_participantaddress",
            "view_appointment",
            "change_appointment",
            "perform_appointment",
            "view_appointmentstatus",
            "add_appointmentstatus",
            "view_screeningepisode",
            "change_screeningepisode",
            "view_participantreportedmammogram",
            "add_participantreportedmammogram",
        ]
    },
}


class PermissionsNotFound(Exception):
    """
    One or more permissions were not found in the database, so couldn't be assigned
    """


def setup_roles():
    """
    Sync the permissions to the Group objects representing our roles.
    """
    for role_name, role_def in ROLES.items():
        group = Group.objects.get(name=role_name)

        for app_label, permission_names in role_def.items():
            permissions = Permission.objects.filter(
                content_type__app_label=app_label, codename__in=permission_names
            )
            if permissions.count() != len(permission_names):
                raise PermissionsNotFound(
                    set(permission_names)
                    - set(permissions.values_list("codename", flat=True))
                )

            existing_permissions = group.permissions.all()

            to_add = set(permissions) - set(existing_permissions)
            to_remove = set(existing_permissions) - set(permissions)

            group.permissions.add(*to_add)
            group.permissions.add(*to_remove)
