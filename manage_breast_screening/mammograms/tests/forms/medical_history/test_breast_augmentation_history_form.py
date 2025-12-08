import datetime
from urllib.parse import urlencode

import pytest
from django.http import QueryDict
from django.test import RequestFactory

from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BreastAugmentationHistoryItemFactory,
)

from ....forms.medical_history.breast_augmentation_history_form import (
    BreastAugmentationHistoryForm,
    BreastAugmentationHistoryUpdateForm,
)


@pytest.mark.django_db
class TestBreastAugmentationHistoryForm:
    def test_no_data(self, clinical_user):
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = BreastAugmentationHistoryForm(QueryDict())

        assert not form.is_valid()
        assert form.errors == {
            "left_breast_procedures": ["Select procedures for the left breast"],
            "right_breast_procedures": ["Select procedures for the right breast"],
        }

    def test_procedure_year_invalid_format(self, clinical_user):
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = BreastAugmentationHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "procedure_year": "qwerty",
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {"procedure_year": ["Enter a whole number."]}

    @pytest.mark.parametrize(
        "selected_breast_procedures",
        [
            [
                BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
            ],
            [
                BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
            ],
            [
                BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES,
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
            ],
        ],
    )
    def test_no_procedures_and_other_options(
        self, clinical_user, selected_breast_procedures
    ):
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = BreastAugmentationHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": selected_breast_procedures,
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "right_breast_procedures": [
                'Unselect "No procedures" in order to select other options'
            ]
        }

        form = BreastAugmentationHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "left_breast_procedures": selected_breast_procedures,
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "left_breast_procedures": [
                'Unselect "No procedures" in order to select other options'
            ]
        }

    def test_removal_year_invalid_format(self, clinical_user):
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = BreastAugmentationHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "implants_have_been_removed": True,
                        "removal_year": "qwerty",
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": [
                "Enter a whole number.",
            ]
        }

    @pytest.mark.parametrize(
        "procedure_year",
        [
            -1,
            1900,
            datetime.date.today().year - 81,
            datetime.date.today().year + 1,
            3000,
        ],
    )
    def test_procedure_year_outside_range(self, clinical_user, procedure_year):
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            (f"Year must be {max_year} or earlier")
            if procedure_year > max_year
            else (f"Year must be {min_year} or later")
        )
        form = BreastAugmentationHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "procedure_year": procedure_year,
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {"procedure_year": [year_outside_range_error_message]}

    @pytest.mark.parametrize(
        "removal_year",
        [
            -1,
            1900,
            datetime.date.today().year - 81,
            datetime.date.today().year + 1,
            3000,
        ],
    )
    def test_removal_year_outside_range(self, clinical_user, removal_year):
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            (f"Year must be {max_year} or earlier")
            if removal_year > max_year
            else (f"Year must be {min_year} or later")
        )
        form = BreastAugmentationHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "implants_have_been_removed": True,
                        "removal_year": removal_year,
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": [
                year_outside_range_error_message,
            ]
        }

    @pytest.mark.parametrize(
        "procedure_year,removal_year",
        [
            (datetime.date.today().year, datetime.date.today().year - 1),
            (datetime.date.today().year - 25, datetime.date.today().year - 30),
            (datetime.date.today().year - 79, datetime.date.today().year - 80),
        ],
    )
    def test_removal_year_before_procedure_year(
        self, clinical_user, procedure_year, removal_year
    ):
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = BreastAugmentationHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "procedure_year": procedure_year,
                        "implants_have_been_removed": True,
                        "removal_year": removal_year,
                    },
                    doseq=True,
                )
            ),
        )

        assert not form.is_valid()
        assert form.errors == {
            "removal_year": ["Year removed cannot be before year of procedure"]
        }

    def test_removal_year_when_not_removed(self, clinical_user):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = BreastAugmentationHistoryForm(
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES
                        ],
                        "procedure_year": 2010,
                        "removal_year": 1900,
                        "additional_details": "removal_year provided but implants_have_been_removed is False",
                    },
                    doseq=True,
                )
            ),
        )

        # confirm full_clean removes removal_year but keeps procedure_year
        assert form.data["removal_year"] == "1900"
        form.full_clean()
        assert form.data["removal_year"] is None
        assert form.cleaned_data["removal_year"] is None
        assert form.cleaned_data["procedure_year"] == 2010

        assert form.is_valid()

        obj = form.create(appointment=appointment, request=request)

        obj.refresh_from_db()
        assert obj.appointment == appointment
        assert obj.left_breast_procedures == [
            BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES
        ]
        assert obj.right_breast_procedures == [
            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
        ]
        assert obj.procedure_year == 2010
        assert not obj.implants_have_been_removed
        assert obj.removal_year is None
        assert (
            obj.additional_details
            == "removal_year provided but implants_have_been_removed is False"
        )

    @pytest.mark.parametrize(
        "data",
        [
            {
                "right_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "left_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
            },
            {
                "right_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                    BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                ],
                "left_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES
                ],
            },
            {
                "right_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES
                ],
                "left_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                    BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION,
                ],
            },
            {
                "right_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "left_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "procedure_year": 2010,
                "implants_have_been_removed": True,
                "removal_year": 2015,
                "additional_details": "Some additional details",
            },
            {
                "right_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "left_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "procedure_year": 2015,
                "implants_have_been_removed": True,
                "removal_year": 2015,
            },
            {
                "right_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "left_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "procedure_year": 2010,
            },
            {
                "right_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "left_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "implants_have_been_removed": True,
                "removal_year": 2015,
            },
            {
                "right_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "left_breast_procedures": [
                    BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                ],
                "implants_have_been_removed": True,
            },
        ],
    )
    def test_success(self, clinical_user, data):
        appointment = AppointmentFactory()
        request = RequestFactory().get("/test-form")
        request.user = clinical_user

        form = BreastAugmentationHistoryForm(
            QueryDict(urlencode(data, doseq=True)),
        )

        assert form.is_valid()

        existing_log_count = AuditLog.objects.count()
        obj = form.create(appointment=appointment, request=request)
        assert AuditLog.objects.count() == existing_log_count + 1
        audit_log = AuditLog.objects.filter(
            object_id=obj.pk, operation=AuditLog.Operations.CREATE
        ).first()
        assert audit_log.actor == clinical_user

        obj.refresh_from_db()
        assert obj.appointment == appointment
        assert obj.left_breast_procedures == data.get("left_breast_procedures")
        assert obj.right_breast_procedures == data.get("right_breast_procedures")
        assert obj.procedure_year == data.get("procedure_year", None)
        assert obj.implants_have_been_removed == ("implants_have_been_removed" in data)
        assert obj.removal_year == data.get("removal_year", None)
        assert obj.additional_details == data.get("additional_details", "")


@pytest.mark.django_db
class TestBreastAugmentationHistoryUpdateForm:
    @pytest.fixture
    def instance(self):
        return BreastAugmentationHistoryItemFactory(
            right_breast_procedures=[
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
            ],
            left_breast_procedures=[
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
            ],
            procedure_year=2000,
            implants_have_been_removed=False,
        )

    def test_no_data(self, instance):
        form = BreastAugmentationHistoryUpdateForm(instance, QueryDict())

        assert not form.is_valid()
        assert form.errors == {
            "left_breast_procedures": ["Select procedures for the left breast"],
            "right_breast_procedures": ["Select procedures for the right breast"],
        }

    def test_initial(self, instance):
        form = BreastAugmentationHistoryUpdateForm(instance, QueryDict())
        assert form.initial == {
            "right_breast_procedures": [
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
            ],
            "left_breast_procedures": [
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
            ],
            "procedure_year": 2000,
            "removal_year": None,
            "implants_have_been_removed": False,
            "additional_details": "",
        }

    def test_success(self, instance, dummy_request):
        form = BreastAugmentationHistoryUpdateForm(
            instance,
            QueryDict(
                urlencode(
                    {
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION
                        ],
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES
                        ],
                        "procedure_year": "2001",
                        "removal_year": "",
                        "additional_details": "abc",
                    },
                    doseq=True,
                )
            ),
        )

        assert form.is_valid()

        obj = form.update(request=dummy_request)
        assert obj.right_breast_procedures == [
            BreastAugmentationHistoryItem.Procedure.OTHER_AUGMENTATION
        ]
        assert obj.left_breast_procedures == [
            BreastAugmentationHistoryItem.Procedure.NO_PROCEDURES
        ]
        assert obj.procedure_year == 2001
        assert obj.removal_year is None
        assert obj.additional_details == "abc"
