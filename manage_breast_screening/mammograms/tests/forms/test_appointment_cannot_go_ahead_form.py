from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ...forms import AppointmentCannotGoAheadForm


@pytest.mark.django_db
class TestAppointmentCannotGoAheadForm:
    @pytest.mark.parametrize(
        "decision,reinvite_value", [("True", True), ("False", False)]
    )
    def test_reinvite_reflects_form_data(self, decision, reinvite_value, clinical_user):
        appointment = AppointmentFactory()
        assert not appointment.reinvite

        form_data = QueryDict(
            urlencode(
                {
                    "stopped_reasons": ["failed_identity_check"],
                    "decision": decision,
                },
                doseq=True,
            )
        )
        form = AppointmentCannotGoAheadForm(form_data, instance=appointment)
        assert form.is_valid()
        form.save(current_user=clinical_user)
        appointment.refresh_from_db()
        assert appointment.reinvite == reinvite_value

    def test_select_single_reason(self, clinical_user):
        """
        Select a single reason (failed identity check) and provide details for that reason,
        but leave the details fields for the other reasons blank to ensure that only the details for the selected reason are saved to the database
        """

        appointment = AppointmentFactory()

        form_data = QueryDict(
            urlencode(
                {
                    "stopped_reasons": ["failed_identity_check"],
                    "no_mammographer_details": "Details about no mammographer",
                    "technical_issues_details": "Details about technical issues",
                    "mental_health_issue_details": "Details about mental health issue",
                    "failed_identity_check_details": "Details about failed identity check",
                    "language_difficulties_details": "Details about language difficulties",
                    "pain_during_screening_details": "Details about pain during screening",
                    "physical_health_issue_details": "Details about physical health issue",
                    "symptomatic_appointment_details": "Details about symptomatic appointment",
                    "participant_withdrew_consent_details": "Details about participant withdrew consent",
                    "other_details": "Details about other",
                    "decision": "False",
                },
                doseq=True,
            )
        )
        form = AppointmentCannotGoAheadForm(form_data, instance=appointment)
        assert form.is_valid()
        form.save(current_user=clinical_user)
        appointment.refresh_from_db()

        assert appointment.stopped_reasons == {
            "stopped_reasons": ["failed_identity_check"],
            "failed_identity_check_details": "Details about failed identity check",
        }
        assert not appointment.reinvite
        assert (
            appointment.statuses.filter(
                name=AppointmentStatusNames.ATTENDED_NOT_SCREENED,
                created_by=clinical_user,
            ).count()
            == 1
        )

    def test_select_other_reason_without_details(self, clinical_user):
        """
        Confirm details are mandatory for other_details.
        """

        appointment = AppointmentFactory()

        form_data = QueryDict(
            urlencode(
                {
                    "stopped_reasons": ["other"],
                    "other_details": "",
                    "decision": "False",
                },
                doseq=True,
            )
        )
        form = AppointmentCannotGoAheadForm(form_data, instance=appointment)
        assert not form.is_valid()
        assert form.errors == {
            "other_details": ["Explain why this appointment cannot proceed"]
        }
        assert (
            appointment.statuses.filter(
                name=AppointmentStatusNames.ATTENDED_NOT_SCREENED,
                created_by=clinical_user,
            ).count()
            == 0
        )

    def test_select_unknown_reason(self, clinical_user):
        """
        Select a reason which is not in the list of possible choices.
        """

        appointment = AppointmentFactory()

        form_data = QueryDict(
            urlencode(
                {
                    "stopped_reasons": ["made_up_reason"],
                    "made_up_reason_details": "",
                    "decision": "False",
                },
                doseq=True,
            )
        )
        form = AppointmentCannotGoAheadForm(form_data, instance=appointment)
        assert not form.is_valid()
        assert form.errors == {
            "stopped_reasons": [
                "Select a valid choice. made_up_reason is not one of the available choices."
            ]
        }
        assert (
            appointment.statuses.filter(
                name=AppointmentStatusNames.ATTENDED_NOT_SCREENED,
                created_by=clinical_user,
            ).count()
            == 0
        )

    def test_select_all_reasons_with_full_details(self, clinical_user):
        """
        Select all reasons and provide details for each
        """

        appointment = AppointmentFactory()

        form_data = QueryDict(
            urlencode(
                {
                    "stopped_reasons": [
                        "failed_identity_check",
                        "pain_during_screening",
                        "symptomatic_appointment",
                        "participant_withdrew_consent",
                        "physical_health_issue",
                        "mental_health_issue",
                        "language_difficulties",
                        "no_mammographer",
                        "technical_issues",
                        "other",
                    ],
                    "failed_identity_check_details": "Details about failed identity check",
                    "pain_during_screening_details": "Details about pain during screening",
                    "symptomatic_appointment_details": "Details about symptomatic appointment",
                    "participant_withdrew_consent_details": "Details about participant withdrew consent",
                    "physical_health_issue_details": "Details about physical health issue",
                    "mental_health_issue_details": "Details about mental health issue",
                    "language_difficulties_details": "Details about language difficulties",
                    "no_mammographer_details": "Details about no mammographer",
                    "technical_issues_details": "Details about technical issues",
                    "other_details": "Details about other",
                    "decision": "True",
                },
                doseq=True,
            )
        )
        form = AppointmentCannotGoAheadForm(form_data, instance=appointment)
        assert form.is_valid()
        form.save(current_user=clinical_user)
        appointment.refresh_from_db()

        assert appointment.stopped_reasons == {
            "stopped_reasons": [
                "failed_identity_check",
                "pain_during_screening",
                "symptomatic_appointment",
                "participant_withdrew_consent",
                "physical_health_issue",
                "mental_health_issue",
                "language_difficulties",
                "no_mammographer",
                "technical_issues",
                "other",
            ],
            "no_mammographer_details": "Details about no mammographer",
            "technical_issues_details": "Details about technical issues",
            "mental_health_issue_details": "Details about mental health issue",
            "failed_identity_check_details": "Details about failed identity check",
            "language_difficulties_details": "Details about language difficulties",
            "pain_during_screening_details": "Details about pain during screening",
            "physical_health_issue_details": "Details about physical health issue",
            "symptomatic_appointment_details": "Details about symptomatic appointment",
            "participant_withdrew_consent_details": "Details about participant withdrew consent",
            "other_details": "Details about other",
        }
        assert appointment.reinvite
        assert (
            appointment.statuses.filter(
                name=AppointmentStatusNames.ATTENDED_NOT_SCREENED,
                created_by=clinical_user,
            ).count()
            == 1
        )

    def test_select_all_reasons_with_minimum_details(self, clinical_user):
        """
        Select all reasons but only provide details for the 'other' reason,
        as it is the only one that requires details to be provided
        """

        appointment = AppointmentFactory()

        form_data = QueryDict(
            urlencode(
                {
                    "stopped_reasons": [
                        "failed_identity_check",
                        "pain_during_screening",
                        "symptomatic_appointment",
                        "participant_withdrew_consent",
                        "physical_health_issue",
                        "mental_health_issue",
                        "language_difficulties",
                        "no_mammographer",
                        "technical_issues",
                        "other",
                    ],
                    "failed_identity_check_details": "",
                    "pain_during_screening_details": "",
                    "symptomatic_appointment_details": "",
                    "participant_withdrew_consent_details": "",
                    "physical_health_issue_details": "",
                    "mental_health_issue_details": "",
                    "language_difficulties_details": "",
                    "no_mammographer_details": "",
                    "technical_issues_details": "",
                    "other_details": "Details about other",
                    "decision": "True",
                },
                doseq=True,
            )
        )
        form = AppointmentCannotGoAheadForm(form_data, instance=appointment)
        assert form.is_valid()
        form.save(current_user=clinical_user)
        appointment.refresh_from_db()

        assert appointment.stopped_reasons == {
            "stopped_reasons": [
                "failed_identity_check",
                "pain_during_screening",
                "symptomatic_appointment",
                "participant_withdrew_consent",
                "physical_health_issue",
                "mental_health_issue",
                "language_difficulties",
                "no_mammographer",
                "technical_issues",
                "other",
            ],
            "other_details": "Details about other",
        }
        assert appointment.reinvite
        assert (
            appointment.statuses.filter(
                name=AppointmentStatusNames.ATTENDED_NOT_SCREENED,
                created_by=clinical_user,
            ).count()
            == 1
        )
