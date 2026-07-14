from src.validator import is_email

def test_email():
    assert is_email('a@b.com')
    assert not is_email('bad')
