from __future__ import unicode_literals
import re
import io

import pytest

from shorttimeseries.utils import split_stream


split_stream_input = [
    '', ' ', '     ',
    'a', 'a ', ' a', ' a ', '     a ',
    'a b', 'a b ', ' a b', 'a  b', 'a   b', ' a   b  ',
    'aa bb cc',
    'aaaaa', 'aaaaa bbbbb', '    aaaaa       bbbbb     ',
]

@pytest.mark.parametrize('s', split_stream_input)
def test_split_stream_text(s):
    result = list(split_stream(io.StringIO(s), buffer_size=4))
    expected = [b for b in s.split() if b]
    assert result == expected

@pytest.mark.parametrize('s', [s.encode('utf-8') for s in split_stream_input])
def test_split_stream_bytes(s):
    result = list(split_stream(io.BytesIO(s), buffer_size=4))
    expected = [b for b in s.split() if b]
    assert result == expected

