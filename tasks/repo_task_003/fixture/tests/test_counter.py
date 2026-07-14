from src.counter import Counter

def test_inc():
    c = Counter()
    c.inc()
    assert c.value() == 1
