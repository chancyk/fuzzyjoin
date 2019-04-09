===============================
fuzzyjoin
===============================


.. image:: https://img.shields.io/pypi/v/fuzzyjoin.svg
        :target: https://pypi.python.org/pypi/fuzzyjoin

.. image:: https://img.shields.io/travis/chancyk/fuzzyjoin.svg
        :target: https://travis-ci.org/chancyk/fuzzyjoin

.. image:: https://readthedocs.org/projects/fuzzyjoin/badge/?version=latest
        :target: https://fuzzyjoin.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/chancyk/fuzzyjoin/shield.svg
     :target: https://pyup.io/repos/github/chancyk/fuzzyjoin/
     :alt: Updates


Join two tables by a fuzzy comparison of text columns.


* Free software: MIT license
* Documentation: https://fuzzyjoin.readthedocs.io.


Features
--------

* Join two lists of dictionaries returning all matching records
  where the specified fields exceed the threshold.

TODO
----
- [ ] Setup TravisCI.
- [ ] Test transformation and exclude functions.
- [ ] Implement left join and full join.
- [ ] Optionally use python-Levenshtein for speed.
- [ ] Options to read from and write to files.
- [ ] Install as a CLI script.
- [ ] Push 0.1.0 to PyPI.
- [ ] Check that the ID is actually unique.


Credits
---------

This package was created with Cookiecutter_ and the `lgiordani/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`lgiordani/cookiecutter-pypackage`: https://github.com/lgiordani/cookiecutter-pypackage

