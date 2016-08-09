import re
from collections import namedtuple

from ._compat import text_type, bytes
from .utils import split_stream

Timestamp = namedtuple('Timestamp', 'year month day hour minute second')


WHITESPACE_RE = re.compile(r'[ \t\n\r\x0b\x0c]+')
WHITESPACE_BYTES_RE = re.compile(WHITESPACE_RE.pattern.encode('utf-8'))

# Alternatively, r'^([0-9]+)|([0-9]*)#([a-zA-Z0-9_-]*)$' ?
TIMESTAMP_RE = re.compile(r'^([0-9]+|[0-9]*(?=#))(?:#([a-zA-Z0-9_-]*))?$')
TIMESTAMP_BYTES_RE = re.compile(TIMESTAMP_RE.pattern.encode('utf-8'))


def make_slices(length):
    offsets = [
            # year
        2,  # month
        2,  # day
        2,  # hour
        2,  # minute
        2,  # second
    ]
    remaining_count = len(offsets) - length + 1
    offsets = offsets[:length-1]
    start = None
    stop = - sum(offsets)
    for offset in offsets:
        yield slice(start, stop)
        start = stop
        stop += offset
    yield slice(start, None)
    for _ in range(remaining_count):
        yield slice(0, 0)

SLICES = {
    'day': Timestamp(*make_slices(3)),
    'hour': Timestamp(*make_slices(4)),
    'minute': Timestamp(*make_slices(5)),
    'second': Timestamp(*make_slices(6)),
}


def parse_partial(file, precision):
    if isinstance(file.read(0), bytes):
        whitespace_re = WHITESPACE_BYTES_RE
        timestamp_re = TIMESTAMP_BYTES_RE
        empty = bytes()
    else:
        whitespace_re = WHITESPACE_RE
        timestamp_re = TIMESTAMP_RE
        empty = text_type()
    slices = SLICES[precision]

    for text in split_stream(file, whitespace_re):
        match = timestamp_re.match(text)
        if not match:
            raise ValueError("bad timestamp: %r" % text)
        ts, label = match.groups(empty)

        ts = Timestamp(*[int(ts[s]) if ts[s] else None for s in slices])

        yield ts, label

