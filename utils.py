import datetime
from dataclasses import dataclass
from typing import List, Optional

import requests


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


@dataclass
class ContentItem:
    """
    Base interface defining Feed.fetch_all() return type
    """

    url: str
    pub_date: datetime.date
    title: Optional[str] = None
    text: Optional[str] = None
    preview_img_url: Optional[str] = None


class ApiClass:
    SUPPORT_FILTER_BY_DATE: Optional[bool] = False  # Does api allow fetching items with date > self.published_after_param
    published_after_param: Optional[datetime.date] = None
    q: List = list()
    url: str

    def __init__(self, url: str):
        self.url = url
        pass  # TODO Move common patterns of yt & tg

    def __iter__(self): return self
    def __next__(self) -> ContentItem: pass


YT_API_KEY = open('.YT_API_KEY').readline()
YT_API_MAX_RESULTS_PER_PAGE = 50
YT_BASE_API_URL = "https://www.googleapis.com/youtube/v3/search"
TG_BASE_URL = 'https://t.me'
