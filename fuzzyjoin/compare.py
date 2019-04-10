import re
import time

from typing import Callable, List, Iterator, Dict, Set, Tuple
from collections import defaultdict

try:
    import editdistance  # type: ignore
    levenshtein = editdistance.eval

except Exception:
    print("[INFO]: editdistance not found. Using pylev.")
    import pylev  # type: ignore
    levenshtein = pylev.levenshtein

from mypy_extensions import TypedDict

from .collate import default_collate, to_tokens


Match = TypedDict("Match", {"score": float, "record_1": Dict, "record_2": Dict})

# Consecutive digits.
RE_NUMBERS = re.compile(r'\d+')


def default_compare(
    text_1: str, text_2: str, collate_fn: Callable = default_collate
) -> float:
    """Calculate the string difference using `pylev.levenshtein` on
    collated version of :param:`text_1` and :param:`text_2`.

    :meth:`fuzzyjoin.collate.default_collate` will be
    used if `collate_fn` is not specified.

    `default_collate` will remove punction and sort the text tokens.

    :returns: float
        A value closer to 1.0 if the strings are similar, as a ratio of the
        delta over the larger of the two strings.

        1 - (delta / larger)
    """
    text_1_c = collate_fn(text_1)
    text_2_c = collate_fn(text_2)
    t1_len = len(text_1_c)
    t2_len = len(text_2_c)
    larger = t1_len if t1_len >= t2_len else t2_len
    delta = levenshtein(text_1_c, text_2_c)
    if delta >= larger:
        return 0.0
    else:
        return 1 - (delta / larger)


def index_by_ngrams(
    records: List[Dict],
    ngram_size: int,
    index_key: str,
    id_key: str,
    tx_fn: Callable = default_collate,
) -> Dict[str, Set[str]]:
    """Collect the IDs from `id_key` of each ngram from field `index_key`."""
    index: Dict[str, Set[str]] = defaultdict(set)
    for record in records:
        for ngram in to_ngrams(tx_fn(record[index_key]), ngram_size):
            index[ngram].add(record[id_key])

    return dict(index)


def to_ngrams(item: str, ngram_size: int) -> Iterator[str]:
    """Yield the list of ngrams of size `ngram_size`of each token in `text`.

    :yields: str
    """
    for token in to_tokens(item):
        for ngram in token_to_ngrams(token, ngram_size):
            yield ngram


def token_to_ngrams(token: str, ngram_size: int) -> Iterator[str]:
    """Yield the list of ngrams of size `ngram_size` from `token` where a token is
    text that does not contain spaces.

    :yields: str
    """
    start = 0
    end = start + ngram_size
    while end <= len(token):
        yield token[start:end]
        start = start + 1
        end = start + ngram_size


def inner_join(
    table_1: List[dict],
    table_2: List[dict],
    key_1: str,
    key_2: str,
    id_key_1: str,
    id_key_2: str,
    threshold: float,
    ngram_size: int = 3,
    compare_fn: Callable = default_compare,
    tx_fn_1: Callable = lambda x: x,
    tx_fn_2: Callable = lambda x: x,
    exclude_fn: Callable = lambda x, y: False,
    show_progress: bool = True,
    numbers_exact: bool = False,
    numbers_permutation: bool = False,
    numbers_subset: bool = False
) -> List[Match]:
    """Return only the matched record above `threshold`.

    Block the records from `table_2` by ngrams of size `ngram_size`.

    Compare each record from `table_1` with a block from `table_2` where the
    `table_1` record shares an ngram with the `table_2` block. This drastically
    limits the total number of comparisons.

    The default `ngram_size` is 3. Increase this value if join is too slow due
    to large block sizes.
    """
    num_options = sum(
        map(
            lambda x: 1 if x else 0,
            [numbers_exact, numbers_permutation, numbers_subset]
        )
    )
    if num_options >= 2:
        raise Exception("Only one numbers option may be selected.")

    total = 0
    index_2 = {x[id_key_2]: x for x in table_2}
    ngram_index_2 = index_by_ngrams(
        table_2, ngram_size, index_key=key_2, id_key=id_key_2, tx_fn=tx_fn_2
    )

    last_time = time.clock()
    table_1_count = len(table_1)
    matches = []  # type: List[Match]
    matched_ids = set()  # type: Set[Tuple[str, str]]
    for i, record_1 in enumerate(table_1):
        text_1 = tx_fn_1(record_1[key_1])
        for ngram in to_ngrams(text_1, ngram_size):
            ngram_block = ngram_index_2.get(ngram, [])
            for id_2 in ngram_block:
                id_1 = record_1[id_key_1]
                # If already matched, don't compare again.
                if (id_1, id_2) in matched_ids:
                    continue

                # Don't compare if the exclude_fn returns true.
                record_2 = index_2[id_2]
                if exclude_fn(record_1, record_2):
                    continue

                total += 1
                text_2 = tx_fn_2(record_2[key_2])
                if numbers_exact and not compare_numbers_exact(text_1, text_2):
                    continue

                if numbers_permutation and not compare_numbers_permutation(text_1, text_2):
                    continue

                if numbers_subset and not compare_numbers_subset(text_1, text_2):
                    continue

                score = compare_fn(text_1, text_2)
                if score >= threshold:
                    matches.append(
                        {"score": score, "record_1": record_1, "record_2": record_2}
                    )
                    matched_ids.add((id_1, id_2))

        if show_progress:
            t = time.clock()
            if (t - last_time) > 5:
                print(f"[INFO] {i} of {table_1_count} : {t:.2f}s")
                last_time = t

    return matches


def compare_numbers_exact(text_1: str, text_2: str) -> bool:
    """Numbers must appear in same order but without leading zeroes."""
    # Strip leading zeroes from all numbers.
    numbers_1 = [int(x) for x in RE_NUMBERS.findall(text_1)]
    numbers_2 = [int(x) for x in RE_NUMBERS.findall(text_2)]
    if numbers_1 == numbers_2:
        return True
    else:
        return False


def compare_numbers_permutation(text_1: str, text_2: str) -> bool:
    """Numbers match without leading zeroes and independent of order."""
    # Strip leading zeroes from all numbers.
    numbers_1 = sorted([int(x) for x in RE_NUMBERS.findall(text_1)])
    numbers_2 = sorted([int(x) for x in RE_NUMBERS.findall(text_2)])
    if numbers_1 == numbers_2:
        return True
    else:
        return False


def compare_numbers_subset(text_1: str, text_2: str) -> bool:
    """One set of numbers must be a complete subset of the other
    without leading zeroes.
    """
    # Strip leading zeroes from all numbers.
    numbers_1 = set([int(x) for x in RE_NUMBERS.findall(text_1)])
    numbers_2 = set([int(x) for x in RE_NUMBERS.findall(text_2)])
    if numbers_1.issubset(numbers_2) or numbers_2.issubset(numbers_1):
        return True
    else:
        return False


def filter_multiples(id_key: str, matches: List[Match]) -> List[Match]:
    """Returns the list of matches where a left table ID has
    multiple matches in the right table.
    """
    counts: Dict[str, int] = defaultdict(lambda: 0)
    for match in matches:
        id = match["record_1"][id_key]
        counts[id] += 1

    multiples_ids = set(id for id, count in counts.items() if count > 1)
    if len(multiples_ids) == 0:
        return []

    multiples_matches = []
    for match in matches:
        if match["record_1"][id_key] in multiples_ids:
            multiples_matches.append(match)

    return multiples_matches
