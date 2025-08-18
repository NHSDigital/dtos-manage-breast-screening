import pytest


@pytest.mark.django_db
class TestRules:
    def test_rule_requiring_clinical_role(
        self, user, administrative_user, clinical_user
    ):
        user.groups.add()

        assert not user.has_perm("mammograms.perform_mammogram_appointment")
        assert not administrative_user.has_perm(
            "mammograms.perform_mammogram_appointment"
        )
        assert clinical_user.has_perm("mammograms.perform_mammogram_appointment")

    def test_rule_requiring_clinical_or_administrative_role(
        self, user, administrative_user, clinical_user
    ):
        user.groups.add()

        assert not user.has_perm("participants.view_participant_data")
        assert administrative_user.has_perm("participants.view_participant_data")
        assert clinical_user.has_perm("participants.view_participant_data")
