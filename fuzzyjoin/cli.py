# -*- coding: utf-8 -*-
import os
import pdb
import sys
import traceback

import click

from . import io, utils, compare as c

# flake8: noqa


@click.command()
@click.option("-f", "--fields", nargs=2, required=True, help="<left_field> <right_field>")
@click.option("-t", "--threshold", default=0.7, show_default=True, type=click.FLOAT, help="Only return matches above this score.")
@click.option("-o", "--output", help="File to write the matches to.")
@click.option("--multiples", "multiples_file", help="File for left IDs with multiple matches.")
@click.option("--exclude", help="An importable function to exclude matches: fn(left_record, right_record)")
@click.option("--collate", help="An importable function to collate the `fields`: fn(text)")
@click.option("--compare", help="An importable function to compare: fn(left_record, right_record)")
@click.option("--numbers-exact", is_flag=True, help="Numbers and order must match exactly.")
@click.option("--numbers-permutation", is_flag=True, help="Numbers must match but may be out of order.")
@click.option("--numbers-subset", is_flag=True, help="Numbers must be a subset.")
@click.option("--ngram-size", default=3, show_default=True, type=click.INT, help="The ngram size to create blocks with.")
@click.option("--no-progress", "no_progress", is_flag=True, help="Do not show comparison progress.",)
@click.option("--debug", is_flag=True, help="Exit to PDB on exception.")
@click.option("--yes", is_flag=True, help="Yes to all prompts.")
@click.argument("left_csv", required=True)
@click.argument("right_csv", required=True)
def main(
    fields,
    threshold,
    output,
    multiples_file,
    exclude,
    collate,
    compare,
    numbers_exact,
    numbers_permutation,
    numbers_subset,
    ngram_size,
    no_progress,
    debug,
    yes,
    left_csv,
    right_csv,
):
    """Fuzzy join <left_csv> and <right_csv> by <left_field> and <right_field>."""
    try:
        collate_fn = utils.import_function(collate) if collate else None
        exclude_fn = utils.import_function(exclude) if exclude else None
        compare_fn = utils.import_function(compare) if compare else None
        key_1, key_2 = fields
        options = c.Options(
            key_1=key_1,
            key_2=key_2,
            threshold=threshold,
            ngram_size=ngram_size,
            collate_fn=collate_fn or c.identity,
            exclude_fn=exclude_fn or c.compare_two_always_false,
            compare_fn=compare_fn or c.default_compare,
            show_progress=not no_progress,
            numbers_exact=numbers_exact,
            numbers_permutation=numbers_permutation,
            numbers_subset=numbers_subset
        )
        matches = io.inner_join_csv_files(left_csv, right_csv, options)

        if output is None:
            output = "matches.csv"

        if not yes:
            utils.prompt_if_exists(output)

        io.write_matches(matches, output)
        if multiples_file:
            multiples_matches = c.filter_multiples(matches)
            if multiples_matches:
                if not yes:
                    utils.prompt_if_exists(multiples_file)
                io.write_matches(multiples_matches, multiples_file)
                print("[INFO] Wrote multiples: %s" % os.path.abspath(multiples_file))

        print("[INFO] Wrote: %s" % os.path.abspath(output))
    except Exception as e:
        extype, value, tb = sys.exc_info()
        traceback.print_exc()
        if debug:
            pdb.post_mortem(tb)
