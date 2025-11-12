from manage_breast_screening.notifications.models import Appointment
from manage_breast_screening.notifications.presenters.bso_contact_data import (
    BsoContactData,
)
from manage_breast_screening.notifications.presenters.clinic_location_data import (
    ClinicLocationData,
)


class PersonalisationPresenter:
    def __init__(self, appointment: Appointment):
        self.appointment = appointment
        self.clinic = appointment.clinic
        self.appointment_date = self.appointment.starts_at.strftime("%A %-d %B %Y")
        self.appointment_time = self.appointment.starts_at.strftime("%-I:%M%p").lower()
        self.address_fields = self.presented_address_fields()
        self.appointment_location_address = ", ".join(
            [val for val in self.address_fields.values() if val]
        )
        self.clinic_location_data = ClinicLocationData(self.clinic)
        self.bso_contact_data = BsoContactData(self.clinic)

    def present(self) -> dict[str:str]:
        return {
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "appointment_clinic_name": self.titlecase(self.clinic.name),
            "appointment_location_address": self.appointment_location_address,
            "appointment_location_description": "",
            "appointment_location_url": self.clinic_location_data.url,
            "BSO_phone_number": self.bso_contact_data.phone,
            "BSO_email_address": self.bso_contact_data.email,
        } | self.address_fields

    def presented_address_fields(self) -> dict[str:str]:
        return {
            "appointment_location_address1": self.titlecase(self.clinic.address_line_1),
            "appointment_location_address2": self.titlecase(self.clinic.address_line_2),
            "appointment_location_address3": self.titlecase(self.clinic.address_line_3),
            "appointment_location_address4": self.titlecase(self.clinic.address_line_4),
            "appointment_location_address5": self.titlecase(self.clinic.address_line_5),
            "appointment_location_postcode": self.uppercase(self.clinic.postcode),
        }

    @staticmethod
    def titlecase(value):
        return (value or "").title()

    @staticmethod
    def uppercase(value):
        return (value or "").upper()
