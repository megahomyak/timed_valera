import datetime

import pytz

MOSCOW_TIMEZONE = pytz.timezone("Europe/Moscow")


def now():
    return datetime.datetime.now(tz=MOSCOW_TIMEZONE)
