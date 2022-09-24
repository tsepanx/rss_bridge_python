import datetime
import os
import pprint
from dataclasses import dataclass
from typing import List, Optional, Type

import requests
from feedgen.feed import FeedGenerator

from tg_api import TGPostDataclass


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


class Feed:
    ContentItemClass: Type[ContentItem]  # = ContentItem
    api_class: Type[ApiClass]  # = ApiClass

    def __init__(self, url: str):
        self.url = url
        self.api_object = self.api_class(url)

    def fetch_all(self, last_n_entries: int = None, after_date: datetime.date = None) -> List[ContentItem]:
        """
        Base function to get new updates from given feed.
        Must be overridden by every Sub-class.
        :return: List[ContentItem]
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


def gen_rss(
        items: List[Type[ContentItem]],
        feed_url: str,
        feed_title: str,
        feed_desc: str = None):
    fg = FeedGenerator()

    fg.id(feed_url)
    fg.title(f'TG | {feed_title}')
    fg.author({'name': feed_title, 'uri': feed_url})
    fg.link(href=feed_url, rel='alternate')
    # fg.logo(feed.api_object.channel_img_url)
    if feed_desc:
        fg.subtitle(feed_desc)
    # fg.link(href='https://larskiesow.de/test.atom', rel='self')
    # fg.language('en')

    for i in items:
        dt = datetime.datetime.combine(
            i.pub_date,
            datetime.time.min,
            datetime.timezone.utc
        )

        if isinstance(i, TGPostDataclass):  # Make tg preview link as rss item link
            link = i.preview_link_url if i.preview_link_url else i.url
        else:
            link = i.url

        if i.html_content:
            content = i.html_content
            content_type = 'html'
        else:
            content = i.text
            content_type = None

        fe = fg.add_entry()
        fe.id(i.url)
        fe.title(shortened_text(i.text, 50))
        fe.content(content, type=content_type)
        fe.link(href=link)
        if i.preview_img_url:
            fe.link(
                href=i.preview_img_url,
                rel='enclosure',
                type=f"media/{i.preview_img_url[i.preview_img_url.rfind('.') + 1:]}"
            )
        fe.published(dt)

    # dirname = f'feeds/{feed_title.replace(" ", "_")}'
    dirname = f'feeds/{feed_title}'
    if not os.path.exists('feeds'):
        os.mkdir('feeds')

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    fg.atom_file(f'{dirname}/atom.xml')  # Write the ATOM feed to a file
    fg.rss_file(f'{dirname}/rss.xml')  # Write the RSS feed to a file


week_delta = datetime.timedelta(days=7)
last_n_weeks = lambda n: datetime.date.today() - n * week_delta