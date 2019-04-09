import csv

from . import compare, utils


def inner_join_files(left_file, right_file, **kwargs):
    left_records = utils.load_csv_as_records(left_file)
    right_records = utils.load_csv_as_records(right_file)
    return compare.inner_join(table_1=left_records, table_2=right_records, **kwargs)


def write_matches(matches, output_file):
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
