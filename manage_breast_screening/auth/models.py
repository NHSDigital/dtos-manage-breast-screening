from dataclasses import dataclass


@dataclass
class Persona:
    first_name: str
    last_name: str
    group: str

    @property
    def username(self):
        return f"{self.first_name.lower()}_{self.last_name.lower()}"


ADMINISTRATIVE_PERSONA = Persona("Anna", "Davies", "Administrative")
CLINICAL_PERSONA = Persona("Chloë", "Robinson", "Clinical")
SUPERUSER_PERSONA = Persona("Simon", "O'Brien", "Superuser")
PERSONAS = [ADMINISTRATIVE_PERSONA, CLINICAL_PERSONA, SUPERUSER_PERSONA]
