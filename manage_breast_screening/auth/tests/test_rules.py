import pytest

from manage_breast_screening.auth.models import Permission


@pytest.mark.django_db
class TestRules:
    def test_rule_requiring_clinical_role(
        self, user, administrative_user, clinical_user, superuser
    ):
        user.groups.add()

        assert not user.has_perm(Permission.PERFORM_MAMMOGRAM_APPOINTMENT)
        assert not administrative_user.has_perm(
            Permission.PERFORM_MAMMOGRAM_APPOINTMENT
        )
        assert clinical_user.has_perm(Permission.PERFORM_MAMMOGRAM_APPOINTMENT)
        assert superuser.has_perm(Permission.PERFORM_MAMMOGRAM_APPOINTMENT)

    def test_rule_requiring_clinical_or_administrative_role(
        self, user, administrative_user, clinical_user, superuser
    ):
        user.groups.add()

        assert not user.has_perm(Permission.VIEW_PARTICIPANT_DATA)
        assert administrative_user.has_perm(Permission.VIEW_PARTICIPANT_DATA)
        assert clinical_user.has_perm(Permission.VIEW_PARTICIPANT_DATA)
        assert superuser.has_perm(Permission.VIEW_PARTICIPANT_DATA)
