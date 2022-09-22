import dataclasses
from datetime import datetime, date
import re
from typing import List, Optional

import requests.status_codes

from utils import shortened_text, logged_get, ContentItem, ApiClass, YT_API_KEY, YT_BASE_API_URL, \
    YT_API_MAX_RESULTS_PER_PAGE


def to_yt_datetime_param(d: date) -> str:
    return datetime.combine(
        d,
        datetime.min.time()
    ).isoformat() + 'Z'

def from_yt_datetime_to_date(s: str) -> date:
    s = s[:-1]  # <- Removing last 'Z' character that leads to errors
    return datetime.fromisoformat(s).date()

@dataclasses.dataclass
class YTVideoDataclass(ContentItem):
    def __repr__(self):
        return f'{self.url} | {shortened_text(self.title)} | {self.pub_date}'

class _ApiFields:
    PAGE_TOKEN = "pageToken"
    NEXT_PAGE_TOKEN = "nextPageToken"
    PUBLISHED_AFTER = "publishedAfter"

class YTApiChannel(ApiClass):
    q: List[dict] = list()
    next_page_token: str = ''
    published_after: Optional[date] = None

    def __init__(self, url: str):
        super().__init__(
            url=url
        )

    @property
    def id(self):
        r = '(?<=channel\/)([A-z]|[0-9])+'
        return re.search(r, self.url).group()

    # --- Iterator related funcs ---

    @staticmethod
    def item_json_to_dataclass(json: dict) -> YTVideoDataclass:
        video_id = json["id"]["videoId"]
        url = f'https://www.youtube.com/watch?v={video_id}'

        date_str = json['snippet']['publishedAt']
        pub_date = from_yt_datetime_to_date(date_str)

        title = json['snippet']['title']
        preview_img_url = json['snippet']['thumbnails']['medium']['url']

        return YTVideoDataclass(
            url=url,
            pub_date=pub_date,
            title=title,
            preview_img_url=preview_img_url
        )

    def fetch_next_page(self, page_token: str = None):
        _params = {
            "key": YT_API_KEY,
            "channelId": self.id,
            "maxResults": YT_API_MAX_RESULTS_PER_PAGE,
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

        print('Making YT request...')

        req = logged_get(YT_BASE_API_URL, _params)

        if req.status_code == 200:
            json = req.json()
            json_items = json.get('items')

            self.next_page_token = json.get(_ApiFields.NEXT_PAGE_TOKEN, None)
            self.q.extend(json_items)
        elif req.status_code == 403:  # Forbidden
            raise Exception('=== YT API FORBIDDEN ===')

    def __iter__(self, published_after: date = None):
        if published_after:
            self.published_after = published_after
        return self

    def __next__(self) -> YTVideoDataclass:
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
    gen = YTApiChannel("https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg").__iter__(
        published_after=date(2022, 9, 15)
    )

    videos_list = list(gen)

    for i in range(len(videos_list)):
        # c = next(gen)
        c = videos_list[i]
        print(c)
