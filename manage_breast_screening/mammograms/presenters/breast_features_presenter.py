class BreastFeaturesPresenter:
    def __init__(self, breast_features):
        self._features = breast_features.annotations_json
        self.feature_count = len(self._features)
