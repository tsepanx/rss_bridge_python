import dataclasses
from datetime import datetime, date
import re
from typing import List, Optional

from tg_api import logged_get, ContentItem

API_KEY = open('.YT_API_KEY').readline()
BASE_API_URL = "https://www.googleapis.com/youtube/v3/search"

def as_list(func):
    def wrapper(*args, **kwargs):
        res = list(func(*args, *kwargs))
        return res
    return wrapper

def _api_get_method(api_url: str, _params: dict) -> dict:
    print('Making request...')

    params = {"key": API_KEY}
    params.update(_params)

    req = logged_get(api_url, params=params)
    return req.json()


def to_yt_datetime_param(d: date) -> str:
    return datetime.combine(
        d,
        datetime.min.time()
    ).isoformat() + 'Z'

def from_yt_datetime_to_date(s: str) -> date:
    s = s[:-1]  # <- Removing last 'Z' character that leads to errors
    return datetime.fromisoformat(s).date()

@dataclasses.dataclass
class YTVideo(ContentItem):
    pass

class _ApiFields:
    PAGE_TOKEN = "pageToken"
    NEXT_PAGE_TOKEN = "nextPageToken"
    PUBLISHED_AFTER = "publishedAfter"

class YTChannelGen:
    q: List[dict] = list()
    next_page_token: str = ''
    published_after: Optional[date] = None

    def __init__(self, url):
        self.url = url

    @property
    def id(self):
        r = '(?<=channel\/)([A-z]|[0-9])+'
        return re.search(r, self.url).group()

    # --- Iterator related funcs ---

    @staticmethod
    def item_json_to_dataclass(json: dict) -> YTVideo:
        video_id = json["id"]["videoId"]
        url = f'https://www.youtube.com/watch?v={video_id}'

        date_str = json['snippet']['publishedAt']
        pub_date = from_yt_datetime_to_date(date_str)

        title = json['snippet']['title']
        preview_img_url = json['snippet']['thumbnails']['medium']['url']

        return YTVideo(
            url=url,
            pub_date=pub_date,
            title=title,
            preview_img_url=preview_img_url
        )

    def fetch_next_page(self, page_token: str = None):
        MAX_RESULTS_PER_PAGE = 50

        _params = {
            "channelId": self.id,
            "maxResults": MAX_RESULTS_PER_PAGE,
            "order": "date",
            "part": "snippet",
            "type": "video",
        }

        if page_token:
            _params.update({
                _ApiFields.PAGE_TOKEN: page_token
            })

        if self.published_after:
            _params.update({
                    _ApiFields.PUBLISHED_AFTER: to_yt_datetime_param(self.published_after)
                })

        json = _api_get_method(BASE_API_URL, _params)
        json_items = json.get('items')

        self.next_page_token = json.get(_ApiFields.NEXT_PAGE_TOKEN, None)
        self.q.extend(json_items)

    def __iter__(self, published_after: date = None):
        if published_after:
            self.published_after = published_after
        return self

    def __next__(self) -> YTVideo:
        if len(self.q) > 0:
            head_elem = self.q.pop(0)
            dataclass_item = self.item_json_to_dataclass(head_elem)

            return dataclass_item
        elif self.next_page_token is None:
            raise StopIteration
        else:
            self.fetch_next_page(self.next_page_token)
            return self.__next__()


if __name__ == "__main__":
    gen = YTChannelGen("https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg").__iter__(
        published_after=date(2022, 9, 15)
    )

    videos_list = list(gen)

    for i in range(len(videos_list)):
        # c = next(gen)
        c = videos_list[i]
        short_title = c.title[:20].replace("\n", " ") + '...'
        print(f'{i + 1} | {c.url} {short_title} {c.pub_date}')
