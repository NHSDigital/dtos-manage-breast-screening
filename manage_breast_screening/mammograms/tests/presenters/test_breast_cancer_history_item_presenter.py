from manage_breast_screening.mammograms.presenters.breast_cancer_history_item_presenter import (
    BreastCancerHistoryItemPresenter,
)
from manage_breast_screening.participants.models.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    BreastCancerHistoryItemFactory,
)


class TestBreastCancerHistoryItemPresenter:
    def test_single(self):
        item = BreastCancerHistoryItemFactory.build(
            diagnosis_location=BreastCancerHistoryItem.DiagnosisLocationChoices.RIGHT_BREAST,
            right_breast_procedure=BreastCancerHistoryItem.Procedure.LUMPECTOMY,
            intervention_location=BreastCancerHistoryItem.InterventionLocation.NHS_HOSPITAL,
            intervention_location_details="East Tester Hospital",
            additional_details="some details",
        )

        presenter = BreastCancerHistoryItemPresenter(item)

        assert presenter.summary_list_params == {
            "rows": [
                {
                    "key": {
                        "text": "Cancer location",
                    },
                    "value": {
                        "html": "Right breast",
                    },
                },
                {
                    "key": {
                        "text": "Procedures",
                    },
                    "value": {
                        "html": "Right breast: Lumpectomy<br>Left breast: No procedure",
                    },
                },
                {
                    "key": {
                        "text": "Other surgery",
                    },
                    "value": {
                        "html": "Right breast: No surgery<br>Left breast: No surgery",
                    },
                },
                {
                    "key": {
                        "text": "Treatment",
                    },
                    "value": {
                        "html": "Right breast: No radiotherapy<br>Left breast: No radiotherapy<br>Systemic treatements: No systemic treatments",
                    },
                },
                {
                    "key": {
                        "text": "Treatment location",
                    },
                    "value": {
                        "html": "At an NHS hospital: East Tester Hospital",
                    },
                },
                {
                    "key": {
                        "text": "Additional details",
                    },
                    "value": {
                        "html": "some details",
                    },
                },
            ],
        }
