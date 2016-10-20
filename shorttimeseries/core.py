import re
from collections import namedtuple
from datetime import datetime, timedelta

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


def fill_partial(timestamps, initial=None):
    timestamps = iter(timestamps)
    if not initial:
        initial, label = next(timestamps)
        yield initial, label

    # TODO: initial shouldn't have gaps
    # TODO: initial might need to be padded with zeroes if < full precision

    for ts, label in timestamps:

        new_ts = []

        have_values = False
        replace_rest = False
        replace_zero = False
        carry = None

        for i, part in enumerate(ts):
            first_value = False

            if part is None:
                if have_values:
                    raise ValueError("can't have gaps: {}, index {}".format(ts, i))
                part = initial[i]
            else:
                first_value = not have_values
                have_values = True

            assert bool(replace_rest) + bool(replace_zero) <= 1

            if replace_rest:
                new_ts.append(part)
                continue

            if replace_zero:
                new_ts.append(1 if i <= 2 else 0) # "zero" is 1 for months/days
                continue

            if part == initial[i]:
                new_ts.append(part)
                continue

            if part > initial[i]:
                new_ts.append(part)
                replace_rest = True
                continue

            if part < initial[i]:
                if first_value:
                    new_ts.append(part)
                    replace_zero = True
                    carry = i
                    # FIXME: new_ts[-1] += 1 # carry one
                else:
                    raise ValueError("can't go backwards: {}, index {}".format(ts, i))
                    # TODO: what do if you *can* go backwards? replace_rest?
                continue

            assert False, "shouldn't get here"

        if carry == 0:
            assert False, "shouldn't get here" # because it would be first_value
        elif carry == 1:
            new_ts[0] = new_ts[0] + 1
        elif carry == 2:
            if new_ts[1] < 12:
                new_ts[1] = new_ts[1] + 1
            else:
                new_ts[1] = 0
                new_ts[0] = new_ts[0] + 1
        elif carry is not None:
            if carry == 3:
                delta = timedelta(days=1)
            elif carry == 4:
                delta = timedelta(hours=1)
            elif carry == 5:
                delta = timedelta(minutes=1)
            else:
                assert False, "shouldn't get here"
            new_ts = (datetime(*new_ts) + delta).timetuple()[0:6]

        yield Timestamp(*new_ts), label


