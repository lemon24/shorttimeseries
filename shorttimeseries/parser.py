from __future__ import unicode_literals
import re
import io
from collections import namedtuple
from datetime import datetime, timedelta

from ._compat import text_type, bytes
from .utils import split_stream


Timestamp = namedtuple('Timestamp', 'year month day hour minute second')
class Timestamp(Timestamp):
    __slots__ = ()
    def __new__(cls, year=None, month=None, day=None, hour=None, minute=None, second=None):
        return super(Timestamp, cls).__new__(cls, year, month, day, hour, minute, second)

FullTimestamp = namedtuple('FullTimestamp', 'timestamp label text')


class TimestampError(Exception):

    def __init__(self, message, timestamp=None):
        super(TimestampError, self).__init__(message)
        self.timestamp = timestamp

    def __str__(self):
        message = super(TimestampError, self).__str__()
        if self.timestamp:
            message = "{}: {!r}".format(message, self.timestamp)
        return message


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
    'day': Timestamp._make(make_slices(3)),
    'hour': Timestamp._make(make_slices(4)),
    'minute': Timestamp._make(make_slices(5)),
    'second': Timestamp._make(make_slices(6)),
}


def parse_partial(file, precision):
    if precision not in SLICES:
        raise ValueError(
            "precision must be one of {!r}, got {!r}"
            .format(tuple(sorted(SLICES)), precision))
    slices = SLICES[precision]

    if isinstance(file, text_type):
        file = io.StringIO(file)
    elif isinstance(file, bytes):
        file = io.BytesIO(file)

    empty = file.read(0)
    if isinstance(empty, bytes):
        timestamp_re = TIMESTAMP_BYTES_RE
    else:
        timestamp_re = TIMESTAMP_RE

    for text in split_stream(file):
        match = timestamp_re.match(text)
        if not match:
            raise TimestampError("invalid timestamp", text)
        ts, label = match.groups(empty)

        ts = Timestamp._make(int(ts[s]) if ts[s] else None for s in slices)

        yield FullTimestamp(ts, label, text)


def parse(file, initial=None, precision='minute'):
    if initial:
        if isinstance(initial, (text_type, bytes)):
            initial_str = initial
            try:
                initial = list(parse_partial(initial, precision))
            except TimestampError as e:
                raise ValueError("initial: %s" % e)
            if len(initial) != 1:
                raise ValueError("initial is not a valid timestamp: %r" % initial_str)
            initial, = initial
            initial = pad_timestamp(initial.timestamp)
            if None in initial:
                raise ValueError("initial is incomplete: %r" % initial_str)
        else:
            try:
                initial = initial.timetuple()[0:6]
            except Exception as e:
                raise ValueError("initial is not a datetime object: %r" % e)
            initial = pad_timestamp(initial)

    timestamps = parse_partial(file, precision)

    if not initial:
        ts = next(timestamps)
        initial = pad_timestamp(ts.timestamp)
        if None in initial:
            raise ValueError(
                "initial not given and the first timestamp is incomplete: {!r}"
                .format(ts.text))
        try:
            yield datetime(*initial), ts.label
        except ValueError as e:
            raise TimestampError(str(e), ts.text)

    for ts in timestamps:
        try:
            initial = fill_timestamp(initial, pad_timestamp(ts.timestamp))
        except TimestampError as e:
            e.timestamp = ts.text
            raise
        try:
            yield datetime(*initial), ts.label
        except ValueError as e:
            raise TimestampError(str(e), ts.text)


def pad_timestamp(timestamp):
    default = Timestamp(0, 1, 1, 0, 0, 0)
    new_timestamp = list(timestamp)
    for i in range(len(timestamp) - 1, -1, -1):
        if new_timestamp[i] is not None:
            break
        new_timestamp[i] = default[i]
    else:
        new_timestamp = timestamp
    return Timestamp._make(new_timestamp)


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
            if first_value and i > 0:
                parts.append(part)
                replace_zero = True
                carry = i
            else:
                raise TimestampError("can't go backwards", timestamp)
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

        try:
            parts = (datetime(*parts) + delta).timetuple()[0:6]
        except ValueError as e:
            raise TimestampError(str(e), timestamp)

    return Timestamp._make(parts)

