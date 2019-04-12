import csv
from typing import List, Any, Dict

from . import compare, utils


def inner_join_csv_files(left_file: str, right_file: str, options: Any) -> List[Dict[str, Any]]:
    """Load the tables from files `left_file` and `right_file` and
    then pass them into `compare.inner_join`.
    """
    left_records = utils.load_csv_as_records(left_file)
    right_records = utils.load_csv_as_records(right_file)
    return compare.inner_join(left_records, right_records, options)


def write_matches(matches: List[compare.Match], output_file: str):
    """Collapse the matches into a single table."""
    with open(output_file, 'w') as out:
        csv_writer = csv.writer(out, lineterminator='\n')
        header_1 = list(matches[0]['record_1'].keys())
        header_2 = list(matches[0]['record_2'].keys())
        header = ['score'] + header_1 + header_2
        csv_writer.writerow(header)
        for match in matches:
            score = match['score']
            record_1 = list(match['record_1'].values())
            record_2 = list(match['record_2'].values())
            csv_writer.writerow([score] + record_1 + record_2)
