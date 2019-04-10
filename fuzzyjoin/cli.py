# -*- coding: utf-8 -*-
import os

import click

from . import io, utils, compare

# flake8: noqa


@click.command()
@click.option("-i", "--ids", nargs=2, required=True, help="<left_id> <right_id>")
@click.option("-f", "--fields", nargs=2, required=True, help="<left_field> <right_field>")
@click.option("-t", "--threshold", default=0.7, show_default=True, type=click.FLOAT, help="Only return matches above this score.")
@click.option("-o", "--output", help="File to write the matches to.")
@click.option("--multiples", help="File to left IDs with multiple matches.")
@click.argument("left_csv", required=True)
@click.argument("right_csv", required=True)
def main(ids, fields, threshold, output, multiples, left_csv, right_csv):
    """Fuzzy join <left_csv> and <right_csv> by <left_field> and <right_field>."""
    key_1, key_2 = fields
    id_key_1, id_key_2 = ids
    matches = io.inner_join_files(
        left_csv,
        right_csv,
        key_1=key_1,
        key_2=key_2,
        id_key_1=id_key_1,
        id_key_2=id_key_2,
        threshold=threshold,
    )
    if output is None:
        output = "matches.csv"

    utils.prompt_if_exists(output)
    io.write_matches(matches, output)
    if multiples:
        multiples_matches = compare.get_multiples(id_key_1, matches)
        if multiples_matches:
            utils.prompt_if_exists(multiples)
            io.write_matches(multiples_matches, multiples)
            print("[Info] Wrote multiples: %s" % os.path.abspath(multiples))

    print("[Info] Wrote: %s" % os.path.abspath(output))
