from django.http import QueryDict
from pytest_django.asserts import assertFormError

from ...forms import ScreeningAppointmentForm


class TestScreeningAppointmentForm:
    def test_decision_cannot_be_left_blank(self):
        form = ScreeningAppointmentForm(QueryDict())
        assertFormError(form, "decision", ["This field is required."])
