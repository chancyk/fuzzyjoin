import csv


def iter_csv_as_records(filepath):
    with open(filepath, 'r') as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader)
        for row in csv_reader:
            yield dict(zip(header, row))


def load_csv_as_records(filepath):
    records = list(iter_csv_as_records(filepath))
    return records
