import re
import itertools

from ._compat import text_type, bytes


WHITESPACE_RE = re.compile(r'[ \t\n\r\x0b\x0c]+')
WHITESPACE_BYTES_RE = re.compile(WHITESPACE_RE.pattern.encode('utf-8'))


def split_stream(file, buffer_size=16*1024):
    """Split the contents of file using runs of whitespace as separator."""

    empty = file.read(0)
    if isinstance(empty, bytes):
        whitespace_re = WHITESPACE_BYTES_RE
    else:
        whitespace_re = WHITESPACE_RE

    chunks = []
    while True:
        buffer = file.read(buffer_size)
        if not buffer:
            break
        parts = whitespace_re.split(buffer)

        if len(parts) == 1:
            chunks.append(parts[0])
            continue

        if parts[0]:
            chunks.append(parts[0])
        if chunks:
            yield empty.join(chunks)
            chunks = []
        for part in itertools.islice(parts, 1, len(parts) - 1):
            yield part
        if parts[-1]:
            chunks.append(parts[-1])

    if chunks:
        yield empty.join(chunks)

