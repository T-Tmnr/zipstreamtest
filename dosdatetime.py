"""
MS-DOS date time format utility

# MS-DOS(FAT) date time

## time format
second: 5bit. precision 2sec.
minute: 6bit
hour: 5bit

## date format
day: 5bit
month: 4bit
year: 7bit. base year is 1980.
"""
from datetime import datetime
from typing import Tuple


def to_dos_datetime(dt: datetime) -> Tuple[int, int]:
    """ Convert datetime to MS-DOS format date and time pair
    :param dt: target datetime
    :return: MS-DOS date time pair
    """
    t = 0
    t += dt.hour
    t <<= 6
    t += dt.minute
    t <<= 5
    t += int(dt.second / 2)
    d = 0
    d += (dt.year - 1980)
    d <<= 4
    d += dt.month
    d <<= 5
    d += dt.day

    return d, t


def from_dos_datetime(d: int, t: int) -> datetime:
    """ Convert datetime to MS-DOS format date and time pair
    :param d: MS-DOS date value
    :param t: MS-DOS time value
    :return: converted datetime
    """
    second = (t & 0b11111) * 2
    t >>= 5
    minute = t & 0b111111
    t >>= 6
    hour = t & 0b11111
    day = d & 0b11111
    d >>= 5
    month = d & 0b1111
    d >>= 4
    year = (d & 0b1111111) + 1980
    return datetime(year, month, day, hour, minute, second)
