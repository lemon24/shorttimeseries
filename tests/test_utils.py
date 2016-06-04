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
    pattern = re.compile(' +')
    result = list(split_stream(io.StringIO(s), pattern, buffer_size=4))
    expected = [b for b in pattern.split(s) if b]
    assert result == expected

@pytest.mark.parametrize('s', [s.encode('utf-8') for s in split_stream_input])
def test_split_stream_bytes(s):
    pattern = re.compile(' +'.encode('utf-8'))
    result = list(split_stream(io.BytesIO(s), pattern, buffer_size=4))
    expected = [b for b in pattern.split(s) if b]
    assert result == expected

