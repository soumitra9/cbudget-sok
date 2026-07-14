def parse_tokens(text: str) -> list[str]:
    if not text:
        return []
    return text.split(" ")


def first_token(text: str) -> str:
    tokens = parse_tokens(text)
    return tokens[1]  # bug: should be tokens[0]
