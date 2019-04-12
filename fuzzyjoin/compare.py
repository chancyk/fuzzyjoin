import re
import time

from typing import Callable, List, Iterator, Dict, Set, Tuple, Any
from collections import defaultdict

try:
    import editdistance  # type: ignore
    levenshtein = editdistance.eval

except Exception:
    print("[INFO]: editdistance not found. Using pylev.")
    import pylev  # type: ignore
    levenshtein = pylev.levenshtein

import attr
from mypy_extensions import TypedDict

from . import utils
from .collate import default_collate, to_tokens


Match = TypedDict("Match", {"score": float, "record_1": Dict, "record_2": Dict})

# Consecutive digits.
RE_NUMBERS = re.compile(r'\d+')


def identity(x):
    return x


def compare_two_always_false(x, y):
    return False


def default_compare(
    text_1: str, text_2: str, options: Any
) -> float:
    comparisons = [
        compare_numbers_exact,
        compare_numbers_permutation,
        compare_numbers_subset,
        compare_fuzzy
    ]
    collate_fn = utils.get(options, 'collate_fn')

    if text_1 == text_2:
        return [{'pass': True, 'score': 1.0}]

    text_1_c = collate_fn(text_1)
    text_2_c = collate_fn(text_2)
    if text_1_c == text_2_c:
        return [{'pass': True, 'score': 1.0}]

    results = []
    for comparison in comparisons:
        result = comparison(text_1_c, text_2_c, options)
        results.append(result)
        if result['pass'] is False:
            return results

    return results


@attr.s(auto_attribs=True)
class Options:
    id_key_1: str
    id_key_2: str
    key_1: str
    key_2: str
    ngram_size: int = 3
    threshold: float = 0.7
    numbers_exact: bool = False
    numbers_permutation: bool = False
    numbers_subset: bool = False
    fuzzy_fn: Callable = levenshtein
    collate_fn: Callable = default_collate
    exclude_fn: Callable = compare_two_always_false
    compare_fn: Callable = default_compare
    show_progress: bool = True


def compare_fuzzy(text_1: str, text_2: str, options: Options):
    fn_name = utils.current_function()
    threshold = utils.get(options, 'threshold')
    fuzzy_fn = utils.get(options, 'fuzzy_fn')

    t1_len = len(text_1)
    t2_len = len(text_2)
    larger = t1_len if t1_len >= t2_len else t2_len
    delta = fuzzy_fn(text_1, text_2)
    if delta >= larger:
        score = 0.0
    else:
        score = 1 - (delta / larger)

    if score >= threshold:
        output = {'pass': True, 'score': score}
    else:
        output = {'pass': False, 'score': score}

    output['meta'] = {
        'function': fn_name,
        'threshold': threshold,
        'fuzzy_fn': fuzzy_fn.__name__
    }
    return output


def compare_numbers_exact(text_1: str, text_2: str, options: Any = None) -> Dict:
    """Numbers must appear in same order but without leading zeroes."""
    fn_name = utils.current_function()
    if options and not utils.get(options, 'numbers_exact'):
        output = {'pass': True}

    # Strip leading zeroes from all numbers.
    numbers_1 = [int(x) for x in RE_NUMBERS.findall(text_1)]
    numbers_2 = [int(x) for x in RE_NUMBERS.findall(text_2)]
    if numbers_1 == numbers_2:
        output = {'pass': True}
    else:
        output = {'pass': False}

    output['meta'] = {'function': fn_name}
    return output


def compare_numbers_permutation(text_1: str, text_2: str, options: Any = None) -> Dict:
    """Numbers match without leading zeroes and independent of order."""
    fn_name = utils.current_function()
    if options and not utils.get(options, 'numbers_permutation'):
        output = {'pass': True}

    # Strip leading zeroes from all numbers.
    numbers_1 = sorted([int(x) for x in RE_NUMBERS.findall(text_1)])
    numbers_2 = sorted([int(x) for x in RE_NUMBERS.findall(text_2)])
    if numbers_1 == numbers_2:
        output = {'pass': True}
    else:
        output = {'pass': False}

    output['meta'] = {'function': fn_name}
    return output


def compare_numbers_subset(text_1: str, text_2: str, options: Any = None) -> bool:
    """One set of numbers must be a complete subset of the other
    without leading zeroes.
    """
    fn_name = utils.current_function()
    if options and not utils.get(options, 'numbers_subset'):
        output = {'pass': True}

    # Strip leading zeroes from all numbers.
    numbers_1 = set([int(x) for x in RE_NUMBERS.findall(text_1)])
    numbers_2 = set([int(x) for x in RE_NUMBERS.findall(text_2)])
    if numbers_1.issubset(numbers_2) or numbers_2.issubset(numbers_1):
        output = {'pass': True}
    else:
        output = {'pass': False}

    output['meta'] = {'function': fn_name}
    return output


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
    options: Any,
) -> List[Match]:
    """Return only the matched record above `threshold`.

    Block the records from `table_2` by ngrams of size `ngram_size`.

    Compare each record from `table_1` with a block from `table_2` where the
    `table_1` record shares an ngram with the `table_2` block. This drastically
    limits the total number of comparisons.

    The default `ngram_size` is 3. Increase this value if join is too slow due
    to large block sizes.
    """
    id_key_1 = utils.get(options, 'id_key_1')
    id_key_2 = utils.get(options, 'id_key_2')
    key_1 = utils.get(options, 'key_1')
    key_2 = utils.get(options, 'key_2')
    ngram_size = utils.get(options, 'ngram_size')
    exclude_fn = utils.get(options, 'exclude_fn')
    collate_fn = utils.get(options, 'collate_fn')
    compare_fn = utils.get(options, 'compare_fn')
    show_progress = utils.get(options, 'show_progress')

    total = 0
    index_2 = {x[id_key_2]: x for x in table_2}
    ngram_index_2 = index_by_ngrams(
        table_2, ngram_size, index_key=key_2, id_key=id_key_2, tx_fn=collate_fn
    )
    last_time = time.clock()
    table_1_count = len(table_1)
    matches = []  # type: List[Match]
    matched_ids = set()  # type: Set[Tuple[str, str]]
    for i, record_1 in enumerate(table_1):
        id_1 = record_1[id_key_1]
        text_1 = collate_fn(record_1[key_1])
        for ngram in to_ngrams(text_1, ngram_size):
            ngram_block = ngram_index_2.get(ngram, [])
            for id_2 in ngram_block:
                total += 1
                # If already matched, don't compare again.
                if (id_1, id_2) in matched_ids:
                    continue

                record_2 = index_2[id_2]
                # Don't compare if the exclude_fn returns true.
                if exclude_fn(record_1, record_2):
                    continue

                text_2 = collate_fn(record_2[key_2])
                results = compare_fn(text_1, text_2, options)
                last_result = results[-1]
                if last_result['pass'] is True:
                    last_result['record_1'] = record_1
                    last_result['record_2'] = record_2
                    matches.append(last_result)
                    matched_ids.add((id_1, id_2))

        if show_progress:
            t = time.clock()
            if (t - last_time) > 5:
                print(f"[INFO] {i} of {table_1_count} : {t:.2f}s")
                last_time = t

    print(f"[INFO] Total comparisons: {total}")
    return matches


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
