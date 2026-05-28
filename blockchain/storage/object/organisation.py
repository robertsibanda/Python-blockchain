"""Organisation data model for managing healthcare organisations and practitioners."""
from dataclasses import dataclass
from typing import Any, Optional

from blockchain.storage import database


@dataclass
class Org:
    """A healthcare organisation with a database-backed member registry."""

    def __init__(self, database: database.Database, organisation_id: str):
        self.database = database
        self.id = organisation_id
        self.pk = self.database.lookup_organisation(self.id)["organisation_pk"]

    def get_practitioner(self, practitioner_id: str) -> Optional[Any]:
        """Look up a practitioner by ID within this organisation.

        Args:
            practitioner_id: The practitioner's unique identifier.

        Returns:
            Practitioner data or None if not found.
        """
        try:
            return self.database.lookup_practitioner(self.id, practitioner_id)
        except Exception as ex:
            print("Exception : " + str(ex))
            return None

    def add_new_member(self, details: Any) -> None:
        """Placeholder: register a new unverified member."""
        pass
