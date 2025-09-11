from manage_breast_screening.forms.choices import YesNo
from manage_breast_screening.mammograms.forms.symptom_forms import (
    LumpForm,
    RightLeftOtherChoices,
    WhenStartedChoices,
)


class TestLumpForm:
    def test_valid_form(self):
        form = LumpForm(
            data={
                "where_located": RightLeftOtherChoices.LEFT_BREAST,
                "how_long": WhenStartedChoices.LESS_THAN_THREE_MONTHS,
                "investigated": YesNo.NO,
            }
        )
        assert form.is_valid()

    def test_missing_required_fields(self):
        form = LumpForm(data={})

        assert not form.is_valid()
        assert form.errors == {
            "how_long": ["This field is required."],
            "investigated": ["This field is required."],
            "where_located": ["This field is required."],
        }

    def test_missing_conditionally_required_fields(self):
        form = LumpForm(
            data={
                "where_located": RightLeftOtherChoices.OTHER,
                "how_long": WhenStartedChoices.SINCE_A_SPECIFIC_DATE,
                "investigated": YesNo.YES,
            }
        )
        assert not form.is_valid()
        assert form.errors == {
            "other_area_description": ["This field is required."],
            "specific_date": ["This field is required."],
            "investigated_details": ["This field is required."],
        }

    def test_valid_form_with_conditionally_required_fields(self):
        form = LumpForm(
            data={
                "where_located": RightLeftOtherChoices.OTHER,
                "how_long": WhenStartedChoices.SINCE_A_SPECIFIC_DATE,
                "investigated": YesNo.YES,
                "other_area_description": "abc",
                "specific_date_0": "2",
                "specific_date_1": "2025",
                "investigated_details": "def",
            }
        )
        assert form.is_valid()

    def test_save(self):
        pass
