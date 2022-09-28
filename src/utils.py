import datetime
import enum
import logging
import os
import random
import time

import pytz as pytz
import requests

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(levelname)s:%(name)s - '%(message)s'"
# )
# logging.getLogger(__name__).debug('Logging configured')
# logging.getLogger('uvicorn.error').propagate = False

# tg_logger = logging.Logger('TG')
# yt_logger = logging.Logger('YT')

DEFAULT_TZ = pytz.UTC

YT_API_KEY = open(os.path.dirname(__file__) + '/../.YT_API_KEY').readline()
YT_API_MAX_RESULTS_PER_PAGE = 50
YT_BASE_API_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YT_BASE_API_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

yt_id_to_url = lambda x: f'https://www.youtube.com/watch?v={x}'
yt_channel_id_to_url = lambda channel_id: f'https://youtube.com/channel/{channel_id}'

TG_BASE_URL = 'https://t.me'
TG_RSS_USE_HTML = True
TG_COMBINE_HTML_WITH_PREVIEW = True
DEFAULT_MAX_ENTRIES_TO_FETCH = 15

RUN_IDENTIFIER = random.randint(1, 1000)

last_n_weeks = lambda n: datetime.date.today() - n * datetime.timedelta(days=7)

class RssFormat(str, enum.Enum):
    Atom = 'atom'
    Rss = 'rss'

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
    print(f'REQUEST: {url}', end=' -> ')
    req = requests.get(url, *args, **kwargs)
    print(f'[{req.status_code}] {req.url}')
    return req

def date_to_datetime(d: datetime.date) -> datetime:
    return datetime.datetime.combine(
        d,
        datetime.datetime.min.time(),
        DEFAULT_TZ
    )

def struct_time_to_datetime(struct: time.struct_time) -> datetime.datetime:
    return datetime.datetime(*struct[:6])

def yt_datetime_to_str_param(d: datetime.date) -> str:
    return datetime.datetime.combine(
        d,
        datetime.datetime.min.time(),
        DEFAULT_TZ
    ).isoformat().replace('+00:00', 'Z')

def yt_str_param_to_datetime(s: str) -> datetime:
    s = s.replace('Z', '+00:00')
    return datetime.datetime.fromisoformat(s)
