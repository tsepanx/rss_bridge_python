import datetime
import enum
import functools
import os
import random
import re
import time
from ssl import SSLError
from typing import Any, TypeVar

import dotenv
import pytz
import requests

DEFAULT_TZ = pytz.UTC
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
RUN_IDENTIFIER = random.randint(1, 1000)

dotenv_vars = dotenv.load_dotenv(".env")

HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", 8081))

USE_YT_API = os.getenv("USE_YT_API", False)

if USE_YT_API:
    YT_API_KEY = os.getenv("YT_API_KEY", None)

    if not YT_API_KEY:
        raise Exception("No Youtube API key specified in env: `YT_API_KEY`")

    YT_API_MAX_RESULTS_PER_PAGE = os.getenv("YT_API_MAX_RESULTS_PER_PAGE", None)
    YT_BASE_API_SEARCH_URL = os.getenv("YT_BASE_API_SEARCH_URL", None)
    YT_BASE_API_VIDEOS_URL = os.getenv("YT_BASE_API_VIDEOS_URL", None)
else:
    YT_API_KEY = None
    YT_API_MAX_RESULTS_PER_PAGE = None
    YT_BASE_API_SEARCH_URL = None
    YT_BASE_API_VIDEOS_URL = None

TG_BASE_URL = os.getenv("TG_BASE_URL", None)
TG_RSS_USE_HTML = os.getenv("TG_RSS_USE_HTML", False)
TG_RSS_HTML_APPEND_PREVIEW = os.getenv("TG_RSS_HTML_APPEND_PREVIEW", False)


def yt_id_to_url(x):
    return f"https://www.youtube.com/watch?v={x}"


def yt_channel_id_to_url(channel_id):
    return f"https://youtube.com/channel/{channel_id}"


def last_n_weeks_date(n: int):
    return datetime.date.today() - n * datetime.timedelta(days=7)


class RssFormat(str, enum.Enum):
    ATOM = "atom"
    RSS = "rss"


DEFAULT_RSS_FORMAT = RssFormat.ATOM


class RssBridgeType(str, enum.Enum):
    TG = "tg"
    YT = "yt"


T = TypeVar("T")


def make_sure(res: Any, return_type: type[T]) -> T | None:
    if isinstance(res, return_type):
        return res
    return None


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
    print("REQUEST -> ", end="")
    try:
        req = requests.get(url, *args, **kwargs)
    except SSLError:
        raise Exception("No connection to the internet")

    print(f"[{req.status_code}] {req.url}")
    return req


def date_to_datetime(d: datetime.date) -> datetime.datetime:
    return datetime.datetime.combine(d, datetime.datetime.min.time(), DEFAULT_TZ)


def struct_time_to_datetime(struct: time.struct_time) -> datetime.datetime:
    return datetime.datetime(*struct[:6])


def yt_datetime_to_str_param(d: datetime.date) -> str:
    return (
        datetime.datetime.combine(d, datetime.datetime.min.time(), DEFAULT_TZ)
        .isoformat()
        .replace("+00:00", "Z")
    )


def yt_str_param_to_datetime(s: str) -> datetime.datetime:
    s = s.replace("Z", "+00:00")
    return datetime.datetime.fromisoformat(s)


def is_youtube_link(s: str):
    return "http" in s or "youtube.com" in s or "youtu.be" in s


def is_youtube_channel_id(s: str):
    return re.search(r"^UC([-_a-zA-Z0-9])+$", s) is not None


def form_preview_html_text(preview_title: str, preview_desc: str) -> str:
    if preview_title or preview_desc:
        return f"<br/>Preview content:<br/>{preview_title}<br/>{preview_desc}"
    return ""
