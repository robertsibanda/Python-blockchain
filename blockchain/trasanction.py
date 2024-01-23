from dataclasses import dataclass, field
from .security import verify_data, create_hash_default


@dataclass
class Transaction:
    type: str
    data: str
    metadata: str
    hash: str
    
    def __post_init__(self):
        self.hash = create_hash_default(self.data)
    
    def verified(self):
        return  # verify_data(self.data, self.metadata['signature'], self.metadata['pk'])
    
    def is_valid(self) -> bool:
        # self.verified()
        return True


@dataclass(frozen=True)
class HashTransaction:
    hash: str
