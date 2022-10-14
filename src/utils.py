import datetime
import enum
import functools
import os
import random
import re
import time
from ssl import SSLError

import pytz
import requests

DEFAULT_TZ = pytz.UTC

SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


YT_API_KEY_PATH = os.path.join(SRC_PATH, ".YT_API_KEY")
if not os.path.exists(YT_API_KEY_PATH):
    with open(YT_API_KEY_PATH, "w") as f:
        try:
            key = os.environ["YT_API_KEY"]
            YT_API_KEY = key
            f.write(key)
        except KeyError:
            raise Exception("No Youtube API key specified: YT_API_KEY")
else:
    with open(YT_API_KEY_PATH, "r") as f:
        YT_API_KEY = f.readline()
YT_API_MAX_RESULTS_PER_PAGE = 50
YT_BASE_API_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YT_BASE_API_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

yt_id_to_url = lambda x: f"https://www.youtube.com/watch?v={x}"
yt_channel_id_to_url = lambda channel_id: f"https://youtube.com/channel/{channel_id}"

TG_BASE_URL = "https://t.me"
TG_RSS_USE_HTML = True
TG_RSS_HTML_APPEND_PREVIEW = True
# DEFAULT_MAX_ENTRIES_TO_FETCH = 15

RUN_IDENTIFIER = random.randint(1, 1000)

last_n_weeks = lambda n: datetime.date.today() - n * datetime.timedelta(days=7)


class RssFormat(str, enum.Enum):
    ATOM = "atom"
    RSS = "rss"


class RssBridgeType(str, enum.Enum):
    TG = "tg"
    YT = "yt"


def get_ttl_hash(seconds=3):
    """Return the same value withing `seconds` time period"""
    return round(time.time() / seconds)


def my_lru_cache(func):
    print("In decorator!")
    new_ttl_hash = get_ttl_hash() + random.randint(1, 100)

    # @functools.wraps(func)
    @functools.lru_cache
    def inner(self, *args, ttl_hash=new_ttl_hash, **kwargs):
        return func(self, *args, **kwargs)

    return inner


def as_list(func):
    def wrapper(*args, **kwargs):
        res = list(func(*args, *kwargs))
        return res

    return wrapper


def shortened_text(s: str, max_chars=20) -> str:
    return s[: min(len(s), max_chars)].strip().replace("\n", " ") + "..."


def logged_get(url, *args, **kwargs):
    print(f"REQUEST -> ", end="")
    try:
        req = requests.get(url, *args, **kwargs)
    except SSLError:
        raise Exception("No connection to the internet")

    print(f"[{req.status_code}] {req.url}")
    return req


def date_to_datetime(d: datetime.date) -> datetime:
    return datetime.datetime.combine(d, datetime.datetime.min.time(), DEFAULT_TZ)


def struct_time_to_datetime(struct: time.struct_time) -> datetime.datetime:
    return datetime.datetime(*struct[:6])


def yt_datetime_to_str_param(d: datetime.date) -> str:
    return (
        datetime.datetime.combine(d, datetime.datetime.min.time(), DEFAULT_TZ)
        .isoformat()
        .replace("+00:00", "Z")
    )


def yt_str_param_to_datetime(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    return datetime.datetime.fromisoformat(s)


def is_youtube_link(s: str):
    return "http" in s or "youtube.com" in s or "youtu.be" in s


def is_youtube_channel_id(s: str):
    return re.search(r"^UC([-_a-zA-Z0-9])+$", s) is not None
