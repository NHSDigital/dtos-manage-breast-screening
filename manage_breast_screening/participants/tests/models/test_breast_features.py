from manage_breast_screening.participants.models.breast_features import (
    BreastFeatureAnnotation,
)


def test_str():
    assert str(
        BreastFeatureAnnotation(
            annotations_json=[
                {"id": "mole", "region_id": "left_upper_inner", "x": 488, "y": 164}
            ]
        )
        == "[{'id': 'mole', 'region_id': 'left_upper_inner', 'x': 488, 'y': 164}]"
    )
