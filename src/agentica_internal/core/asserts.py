__all__ = ['assert_raises']


class assert_raises:
    def __init__(self, *exc_types):
        self.exc_types = exc_types
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, typ, val, tb):
        if typ is None:
            raise AssertionError(f"Expected {self.exc_types} but no exception was raised")
        if not issubclass(typ, self.exc_types):
            return False  # re-raise
        self.value = val
        return True  # suppress
