import dataclasses
import datetime
import re
from typing import List

from tg_api import logged_get

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


@dataclasses.dataclass
class YTVideo:
    url: str
    datetime: datetime.datetime
    title: str
    preview_pic_url: str

class _ApiFields:
    PAGE_TOKEN = "pageToken"
    NEXT_PAGE_TOKEN = "nextPageToken"

class YTChannelGen:
    q: List[dict] = list()
    next_page_token: str = ''

    def __init__(self, url):
        self.url = url

    @property
    def id(self):
        r = '(?<=channel\/)([A-z]|[0-9])+'
        return re.search(r, self.url).group()

    # --- Iterator related funcs ---

    @staticmethod
    def item_json_to_dataclass(json: dict) -> YTVideo:
        # return YTVideo(**json)

        url = f'https://youtube.com/?watch={json["id"]["videoId"]}'
        dt_str = json['snippet']['publishedAt']

        dt = datetime.datetime.fromisoformat(dt_str[:-1])

        title = json['snippet']['title']
        preview_pic_url = json['snippet']['thumbnails']['medium']['url']

        return YTVideo(
            url=url,
            datetime=dt,
            title=title,
            preview_pic_url=preview_pic_url
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

        json = _api_get_method(BASE_API_URL, _params)
        json_items = json.get('items')

        self.next_page_token = json.get(_ApiFields.NEXT_PAGE_TOKEN, None)
        self.q.extend(json_items)

    def __iter__(self):  # TODO Add published_after functionality
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


# if days_after:
#     published_after_datetime = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_after)
#     published_after_string = published_after_datetime.isoformat()
#     print(published_after_string)
#     _params.update({
#         "published_after": published_after_string
#     })

if __name__ == "__main__":
    g = YTChannelGen("https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg")
    for i in range(101):
        v = next(g)
        print(v.url, v.title, v.datetime)
