from dataclasses import dataclass

from blockchain.security import verify_data


@dataclass
class Person:
    name: str


@dataclass
class Patient(Person):
    records: list


@dataclass
class HealthProfessional(Person):
    organisation: str
    role: str
    p_id: str
    public_key: str
    
    def verify_signature(self, signed_data, signature):
        return verify_data(signed_data, signature, self.public_key)
    
    def save(self, db):
        hp_details = {"name": self.name, "pk": self.public_key, "role": self.role,
                      "practitioner_id": self.p_id, "organisation_id": self.organisation
                      }
        
        db.save_practitioners(self.p_id, hp_details)
