import re
from typing import List


# Anything but numbers, digits, and spaces.
RE_PUNCTUATION = re.compile(r"[^a-zA-Z0-9 ]")
# Any consecutive digits.
RE_NUMBERS = re.compile(r"\d+")


def to_tokens(text: str) -> List[str]:
    """Split `text` into a list of words or tokens."""
    return text.split()


def to_sorted_tokens(text: str) -> List[str]:
    """Split `text` into a list of sorted tokens."""
    tokens = to_tokens(text)
    return sorted(tokens)


def default_collate(text: str) -> str:
    """Punctuation is often used a separator, so replace all punctuation with a
    space, and then replace all consecutive spaces with a single space.

    Reodering of words is also common in text, so we will sort the remaining tokens.
    """
    new_text = text
    new_text = RE_PUNCTUATION.sub(" ", new_text)
    new_text = " ".join(to_sorted_tokens(new_text))
    return new_text
