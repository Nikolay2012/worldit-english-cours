import re

APOSTROPHES_PATTERN = re.compile(r"[`’‘]")
TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['-][^\W_]+)*|[^\w\s]")
SPACE_BEFORE_PUNCTUATION_PATTERN = re.compile(r" ([.,!?;:])")


def normalize_spaces(text: str) -> str:
    return " ".join(text.split())


def normalize_sentence(text: str) -> str:
    return normalize_spaces(APOSTROPHES_PATTERN.sub("'", text))


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def join_tokens(tokens: list[str]) -> str:
    return SPACE_BEFORE_PUNCTUATION_PATTERN.sub(r"\1", " ".join(tokens))
