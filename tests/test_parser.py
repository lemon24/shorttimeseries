from __future__ import unicode_literals
import io
from datetime import datetime

import pytest

from shorttimeseries.parser import parse_partial, Timestamp, FullTimestamp
from shorttimeseries.parser import fill_timestamp, pad_timestamp
from shorttimeseries.parser import parse


def test_parse_partial():
    file = io.StringIO("1 12# 123#one #two #")
    assert list(parse_partial(file, 'day')) == [
        FullTimestamp(Timestamp(None, None, 1, None, None, None), '', '1'),
        FullTimestamp(Timestamp(None, None, 12, None, None, None), '', '12#'),
        FullTimestamp(Timestamp(None, 1, 23, None, None, None), 'one', '123#one'),
        FullTimestamp(Timestamp(None, None, None, None, None, None), 'two', '#two'),
        FullTimestamp(Timestamp(None, None, None, None, None, None), '', '#'),
    ]


pad_timestamp_data = [
    (Timestamp(year=2000), Timestamp(2000, 1, 1, 0, 0, 0)),
    (Timestamp(month=2), Timestamp(None, 2, 1, 0, 0, 0)),
    (Timestamp(day=2), Timestamp(None, None, 2, 0, 0, 0)),
    (Timestamp(hour=2), Timestamp(None, None, None, 2, 0, 0)),
    (Timestamp(minute=2), Timestamp(None, None, None, None, 2, 0)),
    (Timestamp(second=2), Timestamp(None, None, None, None, None, 2)),
    (Timestamp(), Timestamp(None, None, None, None, None, None)),
]


@pytest.mark.parametrize('input, expected', pad_timestamp_data)
def test_pad_timestamp(input, expected):
    assert pad_timestamp(input) == expected


initial = Timestamp(2000, 2, 2, 2, 2, 2)
initial_last = Timestamp(2000, 12, 31, 23, 59, 59)

fill_timestamp_data = [
    (initial, Timestamp(second=3), Timestamp(2000, 2, 2, 2, 2, 3)),
    (initial, Timestamp(minute=3), Timestamp(2000, 2, 2, 2, 3, 0)),
    (initial, Timestamp(hour=3), Timestamp(2000, 2, 2, 3, 0, 0)),
    (initial, Timestamp(day=3), Timestamp(2000, 2, 3, 0, 0, 0)),
    (initial, Timestamp(month=3), Timestamp(2000, 3, 1, 0, 0, 0)),
    (initial, Timestamp(year=3000), Timestamp(3000, 1, 1, 0, 0, 0)),

    (initial, Timestamp(second=1), Timestamp(2000, 2, 2, 2, 3, 1)),
    (initial, Timestamp(minute=1), Timestamp(2000, 2, 2, 3, 1, 0)),
    (initial, Timestamp(hour=1), Timestamp(2000, 2, 3, 1, 0, 0)),
    (initial, Timestamp(day=1), Timestamp(2000, 3, 1, 0, 0, 0)),
    (initial, Timestamp(month=1), Timestamp(2001, 1, 1, 0, 0, 0)),
    pytest.mark.xfail(
        (initial, Timestamp(year=1999), Timestamp()),
        raises=ValueError, strict=True), # can't go backwards

    # rollover (e.g. initial minute=59,second=2 and input second=1)
    (initial._replace(minute=59), Timestamp(second=1), Timestamp(2000, 2, 2, 3, 0, 1)),
    (initial._replace(hour=23), Timestamp(minute=1), Timestamp(2000, 2, 3, 0, 1, 0)),
    (initial._replace(day=29), Timestamp(hour=1), Timestamp(2000, 3, 1, 1, 0, 0)),
    (initial._replace(month=12), Timestamp(day=1), Timestamp(2001, 1, 1, 0, 0, 0)),
    (initial_last, Timestamp(second=1), Timestamp(2001, 1, 1, 0, 0, 1)),
    (initial_last, Timestamp(minute=1), Timestamp(2001, 1, 1, 0, 1, 0)),
    (initial_last, Timestamp(hour=1), Timestamp(2001, 1, 1, 1, 0, 0)),

    pytest.mark.xfail(
        (initial._replace(year=2001, day=29), Timestamp(hour=1), Timestamp()),
        raises=ValueError),     # FIXME: wrap the exception from datetime

]


@pytest.mark.parametrize('initial, input, expected', fill_timestamp_data)
def test_fill_timestamp(initial, input, expected):
    assert fill_timestamp(initial, pad_timestamp(input)) == expected


def test_parse():
    assert list(parse('200002020202 1')) == [
        (datetime(2000, 2, 2, 2, 2), ''),
        (datetime(2000, 2, 2, 3, 1), ''),
    ]
    assert list(parse('1', initial=datetime(2000, 2, 2, 2, 2))) == [
        (datetime(2000, 2, 2, 3, 1), ''),
    ]
    assert list(parse('1', initial='200002020202')) == [
        (datetime(2000, 2, 2, 3, 1), ''),
    ]

    with pytest.raises(ValueError):
        list(parse('1'))
    with pytest.raises(ValueError):
        list(parse('1', initial='2'))

    with pytest.raises(ValueError):
        list(parse('200002020202 1', precision='foo'))

