class BaseValidator():
    """Validate values."""
    def __init__(self):
        pass

    def validate(self, value) -> bool: # type: ignore
        pass

class EnumValidator(BaseValidator):
    """Validate whether the value is in defined list."""

    def __init__(self, allowed_values : list):
        """
        Args:
            allowed_values (list): List of allowed values.
        """

        self.__allowed_values = allowed_values

    def validate(self, value) -> bool:
        return (value in self.__allowed_values)