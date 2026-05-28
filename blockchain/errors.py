class BlockInvalidError(Exception):
    """Raised when a block fails integrity or validation checks."""

    def __init__(self, message: str = "Block is invalid"):
        super().__init__(message)
    