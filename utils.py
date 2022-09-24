import datetime
import enum
import pprint
from dataclasses import dataclass
from typing import List, Optional, Type, Sequence, TypeVar

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

class RssFormat(str, enum.Enum):
    Atom = 'atom'
    Rss = 'rss'

@dataclass
class ContentItem:
    """
    Base interface defining Feed.fetch_all() return type
    """

    # id: int  # Unique attr
    url: str
    pub_date: datetime.date
    title: Optional[str] = None
    text: Optional[str] = None
    html_content: Optional[str] = None
    preview_img_url: Optional[str] = None


class ApiClass:
    SUPPORT_FILTER_BY_DATE: Optional[bool] = False  # If api allow fetching items with date > self._published_after_param
    _published_after_param: Optional[datetime.date] = None
    q: List = list()
    url: str
    channel_name: str
    channel_img_url: Optional[str] = None
    channel_desc: Optional[str] = None

    def __init__(self, url: str):
        self.url = url
        self.q = list()  # TODO fix duplicated q within classes
        self.fetch_channel_metadata()
        pass  # TODO Move common patterns of yt & tg

    def __iter__(self):
        return self

    def __next__(self) -> ContentItem: pass

    def fetch_channel_metadata(self) -> str:
        pass


YT_API_KEY = open('.YT_API_KEY').readline()
YT_API_MAX_RESULTS_PER_PAGE = 50
YT_BASE_API_URL = "https://www.googleapis.com/youtube/v3/search"
TG_BASE_URL = 'https://t.me'

# ContentItemType = Type[ContentItem]
ContentItemType = TypeVar('ContentItemType', bound=ContentItem)

class Feed:
    ContentItemClass: Type[ContentItem]  # = ContentItem
    api_class: Type[ApiClass]  # = ApiClass

    def __init__(self, url: str):
        self.url = url
        self.api_object = self.api_class(url)

    def fetch_all(self, last_n_entries: int = None, after_date: datetime.date = None) -> Sequence[ContentItemType]:
        """
        Base function to get new updates from given feed.
        Must be overridden by every Sub-class.
        :return: list of fetched entries
        """
        if after_date:
            if self.api_class.SUPPORT_FILTER_BY_DATE:
                self.api_object._published_after_param = after_date
            else:
                result = list()
                try:
                    while i := next(self.api_object):
                        if i.pub_date > after_date:
                            result.append(i)
                        else:
                            raise StopIteration
                except StopIteration:
                    pprint.pprint(result)
                    return result
                finally:
                    pass

        if last_n_entries:
            result = list()
            for i in range(last_n_entries):
                try:
                    c = next(self.api_object)
                    result.append(c)
                except StopIteration:
                    return result
            return result

        result = list(self.api_object)  # Invokes generator with http requests
        pprint.pprint(result)
        return result


week_delta = datetime.timedelta(days=7)
last_n_weeks = lambda n: datetime.date.today() - n * week_delta
