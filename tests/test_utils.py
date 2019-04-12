from fuzzyjoin import utils


def test_bump_version():
    assert utils.bump_version('0.0.1', part='patch') == '0.0.2'
    assert utils.bump_version('0.0.1', part='minor') == '0.1.0'
    assert utils.bump_version('0.0.1', part='major') == '1.0.0'
    assert utils.bump_version('1.0.1', part='major') == '2.0.0'
    assert utils.bump_version('1.0.1', part='minor') == '1.1.0'
    assert utils.bump_version('1.0.1', part='patch') == '1.0.2'


def test_append_to_stack():
    stack = []
    stack = utils.append_to_stack(stack, 1, size=3)
    assert stack == [1]
    stack = utils.append_to_stack(stack, 2, size=3)
    assert stack == [1, 2]
    stack = utils.append_to_stack(stack, 3, size=3)
    assert stack == [1, 2, 3]
    stack = utils.append_to_stack(stack, 4, size=3)
    assert stack == [2, 3, 4]


def test_import_function():
    fn = utils.import_function('fuzzyjoin.utils.import_function')
    assert fn.__name__ == 'import_function'


def test_yield_chunks():
    chunks = list(utils.yield_chunks([1,2,3,4,5], 2))
    assert chunks[0] == [1, 2]
    assert chunks[1] == [3, 4]
    assert chunks[2] == [5]
