import datetime
from dataclasses import dataclass, field


@dataclass
class HealthObject:
    name: str
    uid: str
    description: str


@dataclass
class Record(HealthObject):
    timestamp: str
    category: str


@dataclass
class Allegie(Record):
    category = "allegy"


@dataclass
class Prescription(Record):
    medicine: str
    quanity: int
    
    def is_patient_allegic(self, patient):
        pass
    
    def drug_to_drug_interaction(self, patient):
        pass
    
    def save(self):
        pass


@dataclass
class Disease(HealthObject):
    disease: str


@dataclass
class Medicine(HealthObject):
    max_dose: int
    chemicals: list


@dataclass
class LabResult(Record):
    category = "lab result"
    result: str


@dataclass
class LabTest(HealthObject):
    test: str
