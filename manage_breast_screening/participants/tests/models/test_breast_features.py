from manage_breast_screening.participants.models.breast_features import (
    BreastFeatureAnnotation,
)


def test_str():
    assert str(
        BreastFeatureAnnotation(annotations_json=[{"x": 1, "y": 1, "name": "abc"}])
        == "[{'x': 1, 'y': 1', 'name': 'abc'}]"
    )
