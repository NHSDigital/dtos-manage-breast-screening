from dataclasses import dataclass


@dataclass
class Persona:
    first_name: str
    last_name: str
    group: str

    @property
    def username(self):
        return f"{self.first_name.lower()}_{self.last_name.lower()}"


ANNA = Persona("Anna", "Davies", "Administrative")
CHLOE = Persona("Chloë", "Robinson", "Clinical")
SIMON = Persona("Simon", "O'Brien", "Superuser")
PERSONAS = [ANNA, CHLOE, SIMON]
