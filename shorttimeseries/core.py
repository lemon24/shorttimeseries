import re
from collections import namedtuple
from datetime import datetime, timedelta

from ._compat import text_type, bytes
from .utils import split_stream

Timestamp = namedtuple('Timestamp', 'year month day hour minute second')
class Timestamp(Timestamp):
    __slots__ = ()
    def __new__(cls, year=None, month=None, day=None, hour=None, minute=None, second=None):
        return super(Timestamp, cls).__new__(cls, year, month, day, hour, minute, second)


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


def fill_partial(timestamps, initial=None):
    timestamps = iter(timestamps)
    if not initial:
        initial, label = next(timestamps)
        initial = pad_timestamp(initial)
        yield initial, label
    else:
        initial = pad_timestamp(initial)

    # TODO: initial shouldn't have gaps

    for timestamp, label in timestamps:
        timestamp = initial = fill_timestamp(initial, pad_timestamp(timestamp))
        yield timestamp, label


def pad_timestamp(timestamp):
    default = Timestamp(0, 1, 1, 0, 0, 0)
    x = []
    it = reversed(list(zip(timestamp, default)))
    for p, d in it:
        if p is not None:
            x.append(p)
            break
        x.append(d)
    x.extend(p for p, _ in it)
    return Timestamp(*reversed(x))


def fill_timestamp(initial, timestamp):
    parts = []

    have_values = False
    replace_rest = False
    replace_zero = False
    carry = None

    for i, part in enumerate(timestamp):
        first_value = False

        if part is None:
            if have_values:
                raise ValueError("can't have gaps: {}, index {}".format(timestamp, i))
            part = initial[i]
        else:
            first_value = not have_values
            have_values = True

        assert bool(replace_rest) + bool(replace_zero) <= 1

        if replace_rest:
            parts.append(part)
            continue

        if replace_zero:
            parts.append(1 if i <= 2 else 0) # "zero" is 1 for months/days
            continue

        if part == initial[i]:
            parts.append(part)
            continue

        if part > initial[i]:
            parts.append(part)
            replace_rest = True
            continue

        if part < initial[i]:
            if first_value:
                parts.append(part)
                replace_zero = True
                carry = i
            else:
                raise ValueError("can't go backwards: {}, index {}".format(timestamp, i))
                # TODO: what do if you *can* go backwards? replace_rest?
            continue

        assert False, "shouldn't get here"

    if carry == 0:
        assert False, "shouldn't get here" # because it would be first_value
    elif carry == 1:
        parts[0] = parts[0] + 1
    elif carry == 2:
        if parts[1] < 12:
            parts[1] = parts[1] + 1
        else:
            parts[1] = 1 # months start with 1
            parts[0] = parts[0] + 1
    elif carry is not None:
        if carry == 3:
            delta = timedelta(days=1)
        elif carry == 4:
            delta = timedelta(hours=1)
        elif carry == 5:
            delta = timedelta(minutes=1)
        else:
            assert False, "shouldn't get here"
        parts = (datetime(*parts) + delta).timetuple()[0:6]

    return Timestamp(*parts)

