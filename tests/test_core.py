from __future__ import unicode_literals
import io

import pytest

from shorttimeseries.core import parse_partial, Timestamp
from shorttimeseries.core import fill_partial


def test_parse_partial():
    file = io.StringIO("1 12# 123#one #two #")
    assert list(parse_partial(file, 'day')) == [
        (Timestamp(None, None, 1, None, None, None), ''),
        (Timestamp(None, None, 12, None, None, None), ''),
        (Timestamp(None, 1, 23, None, None, None), 'one'),
        (Timestamp(None, None, None, None, None, None), 'two'),
        (Timestamp(None, None, None, None, None, None), ''),
    ]


fill_partial_data = [
    ([Timestamp(2000, 1, 1, 0, 0, 0), Timestamp(None, None, None, None, 1, 0)],
        [Timestamp(2000, 1, 1, 0, 0, 0), Timestamp(2000, 1, 1, 0, 1, 0)]),
    pytest.mark.xfail((
        [Timestamp(2000, 1, 1, 0, 0, 0), Timestamp(None, None, None, None, 1, None)],
        [Timestamp(2000, 1, 1, 0, 0, 0), Timestamp(2000, 1, 1, 0, 1, 0)])),
    ([Timestamp(2000, 1, 1, 0, 2, 0), Timestamp(None, None, None, None, 1, 0)],
        [Timestamp(2000, 1, 1, 0, 2, 0), Timestamp(2000, 1, 1, 1, 1, 0)]),
]


@pytest.mark.parametrize('input, expected', fill_partial_data)
def test_fill_partial(input, expected):
    input = [(ts, '') for ts in input]
    output = [ts for ts, _ in fill_partial(input)]
    assert output == expected

