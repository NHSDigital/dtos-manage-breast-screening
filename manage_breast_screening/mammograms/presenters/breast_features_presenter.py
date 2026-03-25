import json


class BreastFeaturesPresenter:
    def __init__(self, breast_features):
        self.features = breast_features.annotations_json
        self.features_json = json.dumps(breast_features.annotations_json)
        self.feature_count = len(breast_features.annotations_json)
        self.diagram_version = breast_features.diagram_version
