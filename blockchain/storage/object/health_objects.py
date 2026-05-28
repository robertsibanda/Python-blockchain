"""Health-related data objects (records, prescriptions, lab results)."""
from dataclasses import dataclass
from typing import List


@dataclass
class HealthObject:
    """Base health data object with name, uid, and description."""
    name: str
    uid: str
    description: str


@dataclass
class Record(HealthObject):
    """A timestamped health record with a category."""
    timestamp: str
    category: str


@dataclass
class Allegie(Record):
    """A patient allergy record."""
    category = "allegy"


@dataclass
class Prescription(Record):
    """A medical prescription with medicine name and quantity."""
    medicine: str
    quanity: int

    def is_patient_allegic(self, patient) -> None:
        """Placeholder: check if patient is allergic to this prescription."""
        pass

    def drug_to_drug_interaction(self, patient) -> None:
        """Placeholder: check for drug-to-drug interactions."""
        pass

    def save(self) -> None:
        """Placeholder: persist prescription."""
        pass


@dataclass
class Disease(HealthObject):
    """A disease record."""
    disease: str


@dataclass
class Medicine(HealthObject):
    """A medicine definition with max dose and chemical composition."""
    max_dose: int
    chemicals: list


@dataclass
class LabResult(Record):
    """A laboratory test result."""
    category = "lab result"
    result: str


@dataclass
class LabTest(HealthObject):
    """A laboratory test definition."""
    test: str
