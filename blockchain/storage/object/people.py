"""People data models: Person, Patient, and HealthProfessional."""
from dataclasses import dataclass
from typing import Any

from blockchain.security import verify_data


@dataclass
class Person:
    """A person with basic identifying information and a public key."""
    firstname: str
    lastname: str
    dob: str
    gender: str
    id_no: str
    address: str
    contact_infor: str
    public_key: str


@dataclass
class Patient:
    """A minimal patient record identified by public key."""
    public_key: str


@dataclass
class HealthProfessional(Person):
    """A healthcare professional affiliated with an organisation."""
    organisation: str
    role: str
    p_id: str
    public_key: str

    def verify_signature(self, signed_data: bytes, signature: bytes) -> bool:
        """Verify a signature using this professional's public key."""
        return verify_data(signed_data, signature, self.public_key)

    def save(self, db: Any) -> None:
        """Persist this health professional's details to the database.

        Args:
            db: Database instance.
        """
        hp_details = {
            "name": self.name, "pk": self.public_key, "role": self.role,
            "practitioner_id": self.p_id, "organisation_id": self.organisation
        }
        db.save_practitioners(self.p_id, hp_details)
