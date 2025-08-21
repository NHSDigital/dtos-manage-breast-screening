from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMINISTRATIVE = "Administrative"
    CLINICAL = "Clinical"
    SUPERUSER = "Superuser"


class Permission(StrEnum):
    VIEW_PARTICIPANT_DATA = "participants.view_participant_data"
    PERFORM_MAMMOGRAM_APPOINTMENT = "mammograms.perform_mammogram_appointment"


@dataclass
class Persona:
    first_name: str
    last_name: str
    group: str

    @property
    def username(self):
        return f"{self.first_name.lower()}_{self.last_name.lower()}"


ADMINISTRATIVE_PERSONA = Persona("Anna", "Davies", Role.ADMINISTRATIVE)
CLINICAL_PERSONA = Persona("Chloë", "Robinson", Role.CLINICAL)
SUPERUSER_PERSONA = Persona("Simon", "O'Brien", Role.SUPERUSER)
PERSONAS = [ADMINISTRATIVE_PERSONA, CLINICAL_PERSONA, SUPERUSER_PERSONA]
