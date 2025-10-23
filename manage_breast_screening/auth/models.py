from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMINISTRATIVE = "Administrative"
    CLINICAL = "Clinical"


class Permission(StrEnum):
    VIEW_PARTICIPANT_DATA = "participants.view_participant_data"
    VIEW_MAMMOGRAM_APPOINTMENT = "mammograms.perform_mammogram_appointment"


@dataclass
class Persona:
    first_name: str
    last_name: str
    role: str

    @property
    def username(self):
        return f"{self.first_name.lower()}_{self.last_name.lower()}"


ADMINISTRATIVE_PERSONA = Persona("Anna", "Davies", Role.ADMINISTRATIVE)
CLINICAL_PERSONA = Persona("Chloë", "Robinson", Role.CLINICAL)
PERSONAS = [ADMINISTRATIVE_PERSONA, CLINICAL_PERSONA]
