
Short Time Series
=================

Short Time Series (STS) is a way of expressing time series that aims to be as
easy to write as possible while remaining unambiguous.


Format
------

A time series is composed of a whitespace-separated stream of timestamps.
Each timestamp may be followed by an optional, user-defined label.

    short-time-series   = *whitespace
                          full-timestamp *( whitespace full-timestamp )
                          *whitespace


### Timestamps

Timestamps are represented as [RFC-3339-style][rfc-3339-format] dates, but
with no separators and with the most significant parts being optional:

    timestamp-day       = [[date-fullyear] date-month] date-mday
    timestamp-hour      = [timestamp-day] time-hour
    timestamp-minute    = [timestamp-hour] time-minute
    timestamp-second    = [timestamp-minute] time-second

    timestamp           = timestamp-day
                        / timestamp-hour
                        / timestamp-minute
                        / timestamp-second

    label               = 1*( ALPHA / DIGIT / "-" / "_" )
    label-timestamp     = timestamp "#" [label]

    empty-timestamp     = "#" [label]

    full-timestamp      = timestamp
                        / label-timestamp
                        / empty-timestamp

Timestamps are not time zone aware (i.e. there is no `time-offset` part). All
other RFC 3339 [restrictions][rfc-3339-restrictions] apply.

Leading zeroes of the leftmost part are optional.

Timestamps may be followed by a number sign ("#") and an optional label. When
the number sign is written, the actual timestamp part may be omitted.

The label should contain only alphanumeric characters and possibly hyphen-minus
and underscore. The number sign is not considered part of the label. If the
number sign and label are missing, the label is a zero-length string.


### Whitespace

Timestamps are separated by one or more ASCII white space characters:

    whitespace          = 1*( SP / HTAB / LF / CR / %x0B / %x0C )


Timestamp precision
-------------------

Timestamps have one of four precisions: `day`, `hour`, `minute`, or `second`.

All timestamps in a series must have the same precision.

When converting a timestamp to a full date, parts below its precision should
have the lowest possible value for that part.



[rfc-3339-format]: https://tools.ietf.org/html/rfc3339#section-5.6
[rfc-3339-restrictions]: https://tools.ietf.org/html/rfc3339#section-5.7
