import datetime
import enum
from datetime import date, datetime, timezone, timedelta

import requests

YT_API_KEY = open('.YT_API_KEY').readline()
YT_API_MAX_RESULTS_PER_PAGE = 50
YT_BASE_API_URL = "https://www.googleapis.com/youtube/v3/search"
TG_BASE_URL = 'https://t.me'

TG_COMBINE_HTML_WITH_PREVIEW = True

last_n_weeks = lambda n: date.today() - n * timedelta(days=7)


def as_list(func):
    def wrapper(*args, **kwargs):
        res = list(func(*args, *kwargs))
        return res

    return wrapper


def shortened_text(s: str, max_chars=20) -> str:
    return s[:min(len(s), max_chars)] \
               .strip() \
               .replace('\n', ' ') \
           + '...'


def logged_get(url, *args, **kwargs):
    print(f'REQUEST: {url}')
    req = requests.get(url, *args, **kwargs)
    print(f'[{req.status_code}] | {req.url}')
    return req


def to_tg_datetime(d: date) -> datetime:
    return datetime.combine(
        d,
        datetime.min.time(),
        timezone.utc
    )


class RssFormat(str, enum.Enum):
    Atom = 'atom'
    Rss = 'rss'

