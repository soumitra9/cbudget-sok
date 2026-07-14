class Calculator:
    """Simple calculator with a deliberate bug for agent tasks."""

    def add(self, a: int, b: int) -> int:
        return a - b  # bug: should add

    def multiply(self, a: int, b: int) -> int:
        return a * b
