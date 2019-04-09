import re


# Anything but numbers, digits, and spaces.
RE_PUNCTUATION = re.compile(r"[^a-zA-Z0-9 ]")
# Any consecutive digits.
RE_NUMBERS = re.compile(r"\d+")
# Consecutive spaces.
RE_SPACES = re.compile(r" +")


def to_tokens(text):
    return [x for x in text.split(" ") if x != ""]


def to_sorted_tokens(text):
    tokens = to_tokens(text)
    return sorted(tokens)


def default_collate(text):
    """Punctuation is often used a separator, so replace all punctuation with a
    space, and then replace all consecutive spaces with a single space.

    Reodering of words is also common in text, so we will sort the remaining tokens.
    """
    new_text = text
    new_text = RE_PUNCTUATION.sub(" ", new_text)
    new_text = RE_SPACES.sub(" ", new_text)
    new_text = " ".join(to_sorted_tokens(new_text))
    return new_text
