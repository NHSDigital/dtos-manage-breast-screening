from manage_breast_screening.mammograms.forms import (
    ProvideSpecialAppointmentDetailsForm,
)

SupportReasons = ProvideSpecialAppointmentDetailsForm.SupportReasons
TemporaryChoices = ProvideSpecialAppointmentDetailsForm.TemporaryChoices


class TestProvideSpecialAppointmentDetailsForm:
    def test_dynamic_form_fields(self):
        form = ProvideSpecialAppointmentDetailsForm()
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
            "any_temporary",
        ]

    def test_valid_form(self):
        form = ProvideSpecialAppointmentDetailsForm(
            data={
                "support_reasons": [SupportReasons.SOCIAL_EMOTIONAL_MENTAL_HEALTH],
                "social_emotional_mental_health_details": "autistic",
                "any_temporary": TemporaryChoices.NO,
            }
        )
        assert form.is_valid()

    def test_conditionally_required_fields(self):
        form = ProvideSpecialAppointmentDetailsForm(
            data={
                "support_reasons": [SupportReasons.HEARING],
                "any_temporary": TemporaryChoices.YES,
            }
        )
        assert not form.is_valid()
        assert form.errors == {"hearing_details": ["Describe the support required"]}

    def test_to_json(self):
        form = ProvideSpecialAppointmentDetailsForm(
            data={
                "support_reasons": [
                    SupportReasons.GENDER_IDENTITY,
                    SupportReasons.PHYSICAL_RESTRICTION,
                ],
                "gender_identity_details": "identifies as male",
                "physical_restriction_details": "uses a mobility aid",
                "any_temporary": TemporaryChoices.NO,
            }
        )
        assert form.is_valid()
        assert form.to_json() == {
            "GENDER_IDENTITY": {"details": "identifies as male", "temporary": False},
            "PHYSICAL_RESTRICTION": {
                "details": "uses a mobility aid",
                "temporary": False,
            },
        }

    def test_init_from_json(self):
        form = ProvideSpecialAppointmentDetailsForm(
            saved_data={
                "MEDICAL_DEVICES": {"details": "has pacemaker", "temporary": False}
            }
        )
        assert form.initial == {
            "support_reasons": [SupportReasons.MEDICAL_DEVICES],
            "medical_devices_details": "has pacemaker",
            "any_temporary": TemporaryChoices.NO,
        }

    def to_and_from_json(self):
        form = ProvideSpecialAppointmentDetailsForm(
            data={
                "support_reasons": [SupportReasons.LANGUAGE],
                "language_details": "speaks french",
                "any_temporary": TemporaryChoices.YES,
            }
        )
        json = form.to_json()
        edit_form = ProvideSpecialAppointmentDetailsForm(saved_data=json)

        assert edit_form.initial == {
            "support_reasons": [SupportReasons.LANGUAGE],
            "language_details": "speaks only french",
            "any_temporary": TemporaryChoices.YES,
        }
