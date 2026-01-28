import pytest

from manage_breast_screening.manual_images.models import Series


class TestSeries:
    @pytest.mark.parametrize(
        "view_position,laterality,expected_string",
        [
            ("CC", "R", "RCC"),
            ("CC", "L", "LCC"),
            ("MLO", "R", "RMLO"),
            ("MLO", "L", "LMLO"),
            ("EKLUND", "R", "Right Eklund"),
            ("EKLUND", "L", "Left Eklund"),
            ("UNKNOWN", "X", "UNKNOWN X"),
        ],
    )
    def test_str_returns_expected_string(
        self, view_position, laterality, expected_string
    ):
        series = Series(view_position=view_position, laterality=laterality)
        assert str(series) == expected_string
