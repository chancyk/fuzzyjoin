import re
import time

from typing import NewType, Callable, List, Iterator, Dict, Set, Tuple, Any
from collections import defaultdict

try:
    import editdistance  # type: ignore
    levenshtein = editdistance.eval

except Exception:
    print("[INFO]: editdistance not found. Using pylev.")
    import pylev  # type: ignore
    levenshtein = pylev.levenshtein

import attr

from .collate import default_collate, to_tokens


Match = NewType("Match", Dict[str, Any])

# Consecutive digits.
RE_NUMBERS = re.compile(r'\d+')


def identity(x):
    return x


def compare_two_always_false(x, y):
    return False


def default_compare(record_1: List[Dict], record_2: List[Dict], options: Any) -> List[Dict]:
    key_1 = options['key_1']
    key_2 = options['key_2']
    collate_fn = options['collate_fn']
    comparisons = [
        compare_numbers_exact,
        compare_numbers_permutation,
        compare_numbers_subset,
        compare_fuzzy
    ]
    text_1 = record_1[key_1]
    text_2 = record_2[key_2]
    if text_1 == text_2:
        return [{'pass': True, 'score': 1.0}]

    text_1_c = collate_fn(text_1)
    text_2_c = collate_fn(text_2)
    if text_1_c == text_2_c:
        return [{'pass': True, 'score': 1.0}]

    results = []
    for comparison in comparisons:
        result = comparison(record_1, record_2, options)  # type: ignore
        results.append(result)
        if result['pass'] is False:
            return results

    return results


def ngram_blocker(table_1: List[Dict], table_2: List[Dict], options: Any):
    id_key_1 = options['id_key_1']
    id_key_2 = options['id_key_2']
    key_1 = options['key_1']
    key_2 = options['key_2']
    ngram_size = options['ngram_size']
    collate_fn = options['collate_fn']

    ngram_index_2 = index_by_ngrams(
        table_2, ngram_size,
        index_key=key_2, id_key=id_key_2,
        tx_fn=collate_fn
    )
    blocks = []
    for record_1 in table_1:
        id_1 = record_1[id_key_1]
        text_1 = collate_fn(record_1[key_1])
        for ngram in to_ngrams(text_1, ngram_size):
            ngram_block = ngram_index_2.get(ngram, [])
            blocks.append((id_1, ngram_block))

    return blocks


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
    blocker_fn: Callable = ngram_blocker
    show_progress: bool = True

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)


def compare_fuzzy(
    record_1: List[Dict], record_2: List[Dict], options: Options
) -> Dict[str, Any]:
    key_1 = options['key_1']
    key_2 = options['key_2']
    threshold = options['threshold']
    fuzzy_fn = options['fuzzy_fn']

    output: Dict[str, Any] = {}
    text_1 = record_1[key_1]
    text_2 = record_2[key_2]
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
        'function': 'compare_fuzzy',
        'threshold': threshold,
        'fuzzy_fn': fuzzy_fn.__name__
    }
    return output


def compare_numbers_exact(
    record_1: List[Dict], record_2: List[Dict], options: Dict[str, Any]
) -> Dict[str, Any]:
    """Numbers must appear in same order but without leading zeroes."""
    meta = {'function': 'compare_numbers_exact'}
    key_1 = options['key_1']
    key_2 = options['key_2']
    if not options['numbers_exact']:
        output = {'pass': True, 'meta': meta}
        return output

    text_1 = record_1[key_1]
    text_2 = record_2[key_2]
    # Strip leading zeroes from all numbers.
    numbers_1 = [int(x) for x in RE_NUMBERS.findall(text_1)]
    numbers_2 = [int(x) for x in RE_NUMBERS.findall(text_2)]
    if numbers_1 == numbers_2:
        output = {'pass': True}
    else:
        output = {'pass': False}

    output['meta'] = meta
    return output


def compare_numbers_permutation(
    record_1: List[Dict], record_2: List[Dict], options: Dict[str, Any]
) -> Dict[str, Any]:
    """Numbers match without leading zeroes and independent of order."""
    meta = {'function': 'compare_numbers_permutation'}
    key_1 = options['key_1']
    key_2 = options['key_2']
    if not options['numbers_permutation']:
        output = {'pass': True, 'meta': meta}
        return output

    text_1 = record_1[key_1]
    text_2 = record_2[key_2]
    # Strip leading zeroes from all numbers.
    numbers_1 = sorted([int(x) for x in RE_NUMBERS.findall(text_1)])
    numbers_2 = sorted([int(x) for x in RE_NUMBERS.findall(text_2)])
    if numbers_1 == numbers_2:
        output = {'pass': True}
    else:
        output = {'pass': False}

    output['meta'] = meta
    return output


def compare_numbers_subset(
    record_1: List[Dict], record_2: List[Dict], options: Dict[str, Any]
) -> Dict[str, Any]:
    """One set of numbers must be a complete subset of the other
    without leading zeroes.
    """
    meta = {'function': 'compare_numbers_subset'}
    key_1 = options['key_1']
    key_2 = options['key_2']
    if not options['numbers_subset']:
        output = {'pass': True, 'meta': meta}
        return output

    text_1 = record_1[key_1]
    text_2 = record_2[key_2]
    # Strip leading zeroes from all numbers.
    numbers_1 = set([int(x) for x in RE_NUMBERS.findall(text_1)])
    numbers_2 = set([int(x) for x in RE_NUMBERS.findall(text_2)])
    if numbers_1.issubset(numbers_2) or numbers_2.issubset(numbers_1):
        output = {'pass': True}
    else:
        output = {'pass': False}

    output['meta'] = meta
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
    table_1: List[Dict],
    table_2: List[Dict],
    options: Any,
) -> List[Dict[str, Any]]:
    """Return only the matched record above `threshold`.

    Block the records from `table_2` by ngrams of size `ngram_size`.

    Compare each record from `table_1` with a block from `table_2` where the
    `table_1` record shares an ngram with the `table_2` block. This drastically
    limits the total number of comparisons.

    The default `ngram_size` is 3. Increase this value if join is too slow due
    to large block sizes.
    """
    options = options.__dict__
    id_key_1 = options['id_key_1']
    id_key_2 = options['id_key_2']
    exclude_fn = options['exclude_fn']
    compare_fn = options['compare_fn']
    blocker_fn = options['blocker_fn']
    show_progress = options['show_progress']

    total = 0
    id_index_1 = {x[id_key_1]: x for x in table_1}
    id_index_2 = {x[id_key_2]: x for x in table_2}
    blocks = blocker_fn(table_1, table_2, options)

    last_time = time.clock()
    matches = []  # type: List[Dict[str, Any]]
    matched_ids = set()  # type: Set[Tuple[str, str]]
    for i, block in enumerate(blocks):
        id_1, block_ids = block
        record_1 = id_index_1[id_1]
        for id_2 in block_ids:
            # If already matched, don't compare again. The same
            # pairs may appear across multiple blocks.
            if (id_1, id_2) in matched_ids:
                continue

            total += 1
            record_2 = id_index_2[id_2]
            if exclude_fn(record_1, record_2):
                continue

            results = compare_fn(record_1, record_2, options)
            last_result = results[-1]
            if last_result['pass'] is True:
                score = last_result['score']
                match = {'score': score, 'record_1': record_1, 'record_2': record_2}
                match['meta'] = {'match_stages': results}
                matches.append(match)
                matched_ids.add((id_1, id_2))

        if show_progress:
            t = time.clock()
            if (t - last_time) > 5:
                print(f"[INFO] {i} of {len(blocks)} : {t:.2f}s")
                last_time = t

    t = time.clock()
    print(f"[INFO] {i} of {len(blocks)} : {t:.2f}s")
    print(f"[INFO] Total comparisons: {total}")
    return matches


def filter_multiples(id_key: str, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
