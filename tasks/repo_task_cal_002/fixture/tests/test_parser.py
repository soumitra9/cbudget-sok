from src.parser import first_token, parse_tokens


def test_parse_tokens():
    assert parse_tokens("a b c") == ["a", "b", "c"]


def test_first_token():
    assert first_token("hello world") == "hello"
