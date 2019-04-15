fuzzyjoin
=========

Join two tables by a fuzzy comparison of text columns.

Features
--------
* Command line utility to quickly join CSV files.
* Ngram blocking to reduce the total number of comparisons.
* Pure python levenshtein edit distance using [pylev](https://github.com/toastdriven/pylev).
* Fast levenshtein edit distance using [editdistance](https://github.com/aflc/editdistance).
* License: [MIT](https://opensource.org/licenses/MIT)


Installation
------------
* Pure python: `pip install fuzzyjoin`
* Optimized: `pip install fuzzyjoin[fast]`


Description
-----------
The goal of this package is to provide a quick and convenient way to
join two tables on a pair of text columns, which often contain variations
of names for the same entity. `fuzzyjoin` satisfies the simple and common case
of joining by a single column from each table for datasets in the thousands of records.

For a more sophisticated and comprehensive treatment of the topic that will allow
you to join records using multiple fields, see the packages below:

* [dedupe](https://github.com/dedupeio/dedupe)
* [recordlinkage](https://recordlinkage.readthedocs.io/en/latest/about.html)


CLI Help
--------
```bash
\> fuzzyjoin --help

Usage: fuzzyjoin_cli.py [OPTIONS] LEFT_CSV RIGHT_CSV

  Inner join <left_csv> and <right_csv> by a fuzzy comparison of
  <left_field> and <right_field>.

Options:
  -f, --fields TEXT...   <left_field> <right_field>  [required]
  -t, --threshold FLOAT  Only return matches above this score.  [default: 0.7]
  -o, --output TEXT      File to write the matches to.
  --multiples TEXT       File for left IDs with multiple matches.
  --exclude TEXT         Function used to exclude records. See:
                         <fuzzyjoin.compare.default_exclude>
  --collate TEXT         Function used to collate <fields>. See:
                         <fuzzyjoin.collate.default_collate>
  --compare TEXT         Function used to compare records. See:
                         <fuzzyjoin.compare.default_compare>
  --numbers-exact        Numbers and order must match exactly.
  --numbers-permutation  Numbers must match but may be out of order.
  --numbers-subset       Numbers must be a subset.
  --ngram-size INTEGER   The ngram size to create blocks with.  [default: 3]
  --no-progress          Do not show comparison progress.
  --debug                Exit to PDB on exception.
  --yes                  Yes to all prompts.
  --help                 Show this message and exit.
```


CLI Usage
---------

```bash
# Use field `name` from left.csv and field `full_name` from right.csv
\> fuzzyjoin --fields name full_name left.csv right.csv
# Export rows with multiple matches from left.csv to a separate file.
\> fuzzyjoin --multiples multiples.csv --fields name full_name left.csv right.csv
# Increase the ngram size, reducing execution time but removing tokens small than `ngram_size`
# as possible matches.
\> fuzzyjoin --ngram-size 5 --fields name full_name left.csv right.csv
# Ensure any numbers that appear are in both fields and in the same order.
\> fuzzyjoin --numbers-exact --fields name full_name left.csv right.csv
# Ensure any numbers that appear are in both fields but may be in a different order.
\> fuzzyjoin --numbers-permutation --fields name full_name left.csv right.csv
# Ensure numbers that appear in one field are at least a subset of the other.
\> fuzzyjoin --numbers-subset --fields name full_name left.csv right.csv
# Use importable function `package.func` from PATH as the comparison function
# instead of `fuzzyjoin.compare.default_compare`.
\> fuzzyjoin --compare package.func --fields name full_name left.csv right.csv
```

API Usage
---------
```python
from fuzzyjoin.io import inner_join_csv_files

options = Options(

)
inner_join_csv_files('left.csv', 'right.csv', )
```

TODO
----
- Test transformation and exclude functions.
- Implement left join and full join.
- Check that the ID is actually unique.
- Add documentation.
- Option to rename headers and disambiguate duplicate header names.


History
=======
0.5.0 (2019-04-15)
------------------
* Removed ID field requirement.

0.4.1 (2019-04-12)
------------------
* Options parameter.

0.3.4 (2019-04-11)
------------------
* Fix function defaults.
* Minor optimizations.
* Additional CLI parameters.

0.3.3 (2019-04-10)
------------------
* Cleanup checks.

0.3.2 (2019-04-10)
------------------
* Include basic installation instructions.

0.3.1 (2019-04-10)
------------------
* Minor README updates.


0.3.0 (2019-04-10)
------------------
* Use editdistance if available, otherwise fallback to pylev.
* Report progress by default.
* Number comparison options.
* Renamed get_multiples to filter_multiples.


0.2.1 (2019-04-10)
------------------
* Additional docs and tests.

0.2.0 (2019-04-09)
------------------
* Write multiples matches to a separate file.
* Added types and docstrings.

0.1.2 (2019-04-09)
------------------
* Duplicate release of 0.1.1

0.1.1 (2019-04-09)
------------------
* First release on PyPI.
