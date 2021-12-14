import datetime

import pytz

MOSCOW_TIMEZONE = pytz.timezone("Europe/Moscow")


def now():
    return datetime.datetime.now(tz=MOSCOW_TIMEZONE)


def decline_word(amount, forms):
    last_digit = amount % 10
    if last_digit == 1 or 11 <= amount <= 19:
        return forms[0]
    elif 2 <= last_digit <= 4:
        return forms[1]
    else:
        return forms[2]
