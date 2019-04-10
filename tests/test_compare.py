from fuzzyjoin import compare


def demo_records():
    return [
        {"id": 1, "text": "a hello world"},
        {"id": 2, "text": "hella"},
        {"id": 3, "text": "zzzz"},
    ]


def test_default_compare():
    assert 1.0 == compare.default_compare("string", "string")
    assert 1.0 == compare.default_compare("hello world", "world-hello.")
    assert 0.8 == compare.default_compare("hello", "hell")
    assert 0.0 == compare.default_compare("hello", "zzzzz")


def test_ngrams():
    records = demo_records()
    index = compare.index_by_ngrams(
        records, index_key="text", id_key="id", ngram_size=4
    )
    # Note that the ngram smaller than `ngram_size` are not
    # included in the index.
    assert "hell" in index
    assert "ello" in index
    assert "worl" in index
    assert "orld" in index
    assert "ella" in index
    assert "zzzz" in index
    assert len(index) == 6
    id_counts = [len(x) for x in index.values()]
    assert sum(id_counts) == 7
    assert index["hell"] == {1, 2}


def test_inner_join():
    threshold = 0.8
    records_1 = demo_records()
    records_2 = demo_records()
    matches = compare.inner_join(
        table_1=records_1,
        table_2=records_2,
        key_1="text",
        key_2="text",
        id_key_1="id",
        id_key_2="id",
        threshold=threshold,
        ngram_size=3,
    )
    assert len(matches) == 3
    # We'll get two exact matches since we're using the
    # same record set twice.
    assert matches[0]["score"] == 1.0
    assert matches[1]["score"] == 1.0
    assert matches[0]["record_1"]["id"] == 1
    assert matches[0]["record_2"]["id"] == 1
    assert matches[1]["record_1"]["id"] == 2
    assert matches[1]["record_2"]["id"] == 2
    below_threshold = [x["score"] for x in matches if x["score"] <= threshold]
    assert len(below_threshold) == 0


def test_inner_join_lower_threshold():
    threshold = 0.1
    records_1 = demo_records()
    records_2 = demo_records()
    matches = compare.inner_join(
        table_1=records_1,
        table_2=records_2,
        key_1="text",
        key_2="text",
        id_key_1="id",
        id_key_2="id",
        threshold=threshold,
        ngram_size=3,
    )
    assert len(matches) == 5
    # We'll get two low scoring approximate matches between
    # "hella" and "a hello world".
    assert matches[1]["score"] < 3.1
    assert matches[1]["record_1"]["id"] == 1
    assert matches[1]["record_2"]["id"] == 2
    assert matches[2]["score"] < 3.1
    assert matches[2]["record_1"]["id"] == 2
    assert matches[2]["record_2"]["id"] == 1


def test_inner_join_multiples():
    threshold = 0.1
    records_1 = demo_records()
    records_2 = demo_records()
    matches = compare.inner_join(
        table_1=records_1,
        table_2=records_2,
        key_1="text",
        key_2="text",
        id_key_1="id",
        id_key_2="id",
        threshold=threshold,
        ngram_size=3,
    )
    multiples = compare.get_multiples(id_key="id", matches=matches)
    assert len(multiples) == 4
