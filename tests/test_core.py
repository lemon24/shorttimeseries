from __future__ import unicode_literals
import io

from shorttimeseries.core import parse_partial, Timestamp


def test_parse_partial():
    file = io.StringIO("1 12# 123#one #two #")
    assert list(parse_partial(file, 'day')) == [
        (Timestamp(None, None, 1, None, None, None), ''),
        (Timestamp(None, None, 12, None, None, None), ''),
        (Timestamp(None, 1, 23, None, None, None), 'one'),
        (Timestamp(None, None, None, None, None, None), 'two'),
        (Timestamp(None, None, None, None, None, None), ''),
    ]
