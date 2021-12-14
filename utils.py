import datetime

import pytz

MOSCOW_TIMEZONE = pytz.timezone("Europe/Moscow")


def now():
    return datetime.datetime.now(tz=MOSCOW_TIMEZONE)


def decline_word(amount, forms):
    amount %= 10
    if amount == 1:
        return forms[0]
    elif 2 <= amount <= 4:
        return forms[1]
    else:
        return forms[2]
