from manage_breast_screening.mammograms.forms import (
    ProvideSpecialAppointmentDetailsForm,
)
from manage_breast_screening.participants.tests.factories import ParticipantFactory

SupportReasons = ProvideSpecialAppointmentDetailsForm.SupportReasons


class TestProvideSpecialAppointmentDetailsForm:
    def test_dynamic_form_fields(self):
        form = ProvideSpecialAppointmentDetailsForm(
            participant=ParticipantFactory.build()
        )
        assert list(form.fields.keys()) == [
            "support_reasons",
            "breast_implants_details",
            "medical_devices_details",
            "vision_details",
            "hearing_details",
            "physical_restriction_details",
            "social_emotional_mental_health_details",
            "language_details",
            "gender_identity_details",
            "other_details",
        ]

    def test_valid_form(self):
        form = ProvideSpecialAppointmentDetailsForm(
            participant=ParticipantFactory.build(),
            data={
                "support_reasons": [SupportReasons.SOCIAL_EMOTIONAL_MENTAL_HEALTH],
                "social_emotional_mental_health_details": "autistic",
            },
        )
        assert form.is_valid()
        assert form.cleaned_data == {
            "breast_implants_details": "",
            "gender_identity_details": "",
            "hearing_details": "",
            "language_details": "",
            "medical_devices_details": "",
            "other_details": "",
            "physical_restriction_details": "",
            "social_emotional_mental_health_details": "autistic",
            "support_reasons": [
                "SOCIAL_EMOTIONAL_MENTAL_HEALTH",
            ],
            "vision_details": "",
        }

    def test_conditionally_required_fields(self):
        form = ProvideSpecialAppointmentDetailsForm(
            participant=ParticipantFactory.build(),
            data={
                "support_reasons": [SupportReasons.HEARING],
            },
        )
        assert not form.is_valid()
        assert form.errors == {"hearing_details": ["Describe the support required"]}

    def test_to_json(self):
        form = ProvideSpecialAppointmentDetailsForm(
            participant=ParticipantFactory.build(),
            data={
                "support_reasons": [
                    SupportReasons.GENDER_IDENTITY,
                    SupportReasons.PHYSICAL_RESTRICTION,
                ],
                "gender_identity_details": "identifies as male",
                "physical_restriction_details": "uses a mobility aid",
            },
        )
        assert form.is_valid()
        assert form.to_json() == {
            "GENDER_IDENTITY": {"details": "identifies as male"},
            "PHYSICAL_RESTRICTION": {
                "details": "uses a mobility aid",
            },
        }

    def test_init_from_json(self):
        form = ProvideSpecialAppointmentDetailsForm(
            participant=ParticipantFactory.build(
                extra_needs={"MEDICAL_DEVICES": {"details": "has pacemaker"}}
            )
        )
        assert form.initial == {
            "support_reasons": [SupportReasons.MEDICAL_DEVICES],
            "medical_devices_details": "has pacemaker",
        }

    def to_and_from_json(self):
        form = ProvideSpecialAppointmentDetailsForm(
            participant=ParticipantFactory.build(
                extra_needs={
                    "support_reasons": [SupportReasons.LANGUAGE],
                    "language_details": "speaks french",
                }
            )
        )
        json = form.to_json()
        edit_form = ProvideSpecialAppointmentDetailsForm(
            participant=ParticipantFactory.build(extra_needs=json)
        )

        assert edit_form.initial == {
            "support_reasons": [SupportReasons.LANGUAGE],
            "language_details": "speaks only french",
        }
