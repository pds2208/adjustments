class SageException(Exception):
    """Raised when a Sage call fails"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
