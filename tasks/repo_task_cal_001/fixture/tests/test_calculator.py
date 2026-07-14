from src.calculator import Calculator


def test_add():
    assert Calculator().add(2, 3) == 5


def test_multiply():
    assert Calculator().multiply(4, 5) == 20
