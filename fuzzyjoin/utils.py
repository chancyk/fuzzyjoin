import csv
from typing import Iterator, Dict, List


def iter_csv_as_records(filepath: str) -> Iterator[Dict[str, str]]:
    """Yield each line of `filepath` as a dict using
    the first line as the keys.
    """
    with open(filepath, 'r') as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader)
        for row in csv_reader:
            yield dict(zip(header, row))


def load_csv_as_records(filepath: str) -> List[Dict[str, str]]:
    """Return a list of dicts using the first line as a
    header for the dictionary keys.
    """
    records = list(iter_csv_as_records(filepath))
    return records
