class NotFoundError(Exception):
    """A requested profile or opportunity does not exist."""

    def __init__(self, what: str) -> None:
        super().__init__(f"{what} not found")
        self.what = what
