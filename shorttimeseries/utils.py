import itertools


def split_stream(file, pattern, buffer_size=16*1024):
    """Streaming version of re.split()."""
    empty = file.read(0)

    chunks = []
    while True:
        buffer = file.read(buffer_size)
        if not buffer:
            break
        parts = pattern.split(buffer)

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

