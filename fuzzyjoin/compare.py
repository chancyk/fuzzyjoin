from typing import Callable, List, Iterator, Dict, Set, Tuple
from collections import defaultdict

import pylev  # type: ignore
from mypy_extensions import TypedDict

from .collate import default_collate, to_tokens


Match = TypedDict("Match", {"score": float, "record_1": Dict, "record_2": Dict})


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
    delta = pylev.levenshtein(text_1_c, text_2_c)
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
) -> List[Match]:
    """Return only the matched record above `threshold`.

    Block the records from `table_2` by ngrams of size `ngram_size`.

    Compare each record from `table_1` with a block from `table_2` where the
    `table_1` record shares an ngram with the `table_2` block. This drastically
    limits the total number of comparisons.

    The default `ngram_size` is 3. Increase this value if join is too slow due
    to large block sizes.
    """
    total = 0
    index_2 = {x[id_key_2]: x for x in table_2}
    ngram_index_2 = index_by_ngrams(
        table_2, ngram_size, index_key=key_2, id_key=id_key_2, tx_fn=tx_fn_2
    )

    matches: List[Match] = []
    matched_ids: Set[Tuple[str, str]] = set()
    for i, record_1 in enumerate(table_1):
        text_1 = tx_fn_1(record_1[key_1])
        for ngram in to_ngrams(text_1, ngram_size):
            ngram_block = ngram_index_2.get(ngram, [])
            for id_2 in ngram_block:
                # If already matched, don't compare again.
                if (record_1[id_key_1], id_2) in matched_ids:
                    continue

                # Don't compare if the exclude_fn returns true.
                record_2 = index_2[id_2]
                if exclude_fn(record_1, record_2):
                    continue

                total += 1
                text_2 = tx_fn_2(record_2[key_2])
                score = compare_fn(text_1, text_2)
                if score >= threshold:
                    matches.append(
                        {"score": score, "record_1": record_1, "record_2": record_2}
                    )
                    matched_ids.add((record_1[id_key_1], record_2[id_key_2]))

    return matches
