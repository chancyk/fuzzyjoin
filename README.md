fuzzyjoin
=========

Join two tables by a fuzzy comparison of text columns.

Features
--------
* Command line utility to quickly join CSV files.
* Ngram blocking to reduce the total number of comparisons.
* Pure python levenshtein edit distance using [pylev](https://github.com/toastdriven/pylev).
* Fast levenshtein edit distance using [editdistance](https://github.com/aflc/editdistance).
  - with: `pip install fuzzyjoin[fast]`
* License: [MIT](https://opensource.org/licenses/MIT)

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


TODO
----
- Test transformation and exclude functions.
- Implement left join and full join.
- Check that the ID is actually unique.
- Add documentation.
- Option to rename headers and disambiguate duplicate header names.


History
=======

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
