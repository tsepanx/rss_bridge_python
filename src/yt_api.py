import dataclasses
import re
from typing import List, Optional, Type

from .base import ApiChannel, ApiItem, ItemDataclass, ItemDataclassType
from .utils import (
    YT_API_KEY,
    YT_API_MAX_RESULTS_PER_PAGE,
    YT_BASE_API_SEARCH_URL,
    YT_BASE_API_VIDEOS_URL,
    logged_get,
    shortened_text,
    yt_channel_id_to_url,
    yt_datetime_to_str_param,
    yt_id_to_url,
    yt_str_param_to_datetime,
)


@dataclasses.dataclass
class YTVideoDataclass(ItemDataclass):
    @classmethod
    def from_raw_data(cls, json: dict) -> Optional["YTVideoDataclass"]:
        video_id = json["id"]["videoId"]
        url = f"https://www.youtube.com/watch?v={video_id}"

        date_str = json["snippet"]["publishedAt"]
        pub_date = yt_str_param_to_datetime(date_str)

        title = json["snippet"]["title"]
        description = json["snippet"]["description"]
        preview_img_url = json["snippet"]["thumbnails"]["medium"]["url"]

        return cls(
            url=url,
            pub_date=pub_date,
            title=title,
            text_content=description,
            preview_img_url=preview_img_url,
        )

    def __repr__(self):
        return f"{self.url} | {shortened_text(self.title, 30)} | {self.pub_date}"


class ApiFieldsEnum:
    PAGE_TOKEN = "pageToken"
    NEXT_PAGE_TOKEN = "nextPageToken"
    PUBLISHED_AFTER = "publishedAfter"


class YTApiChannel(ApiChannel):
    ItemDataclassClass: ItemDataclassType = YTVideoDataclass

    SUPPORT_FILTER_BY_DATE = True
    q: List[dict] = list()
    next_page_token: str = ""

    def __init__(
        self,
        by_url: str = None,
        by_channel_id: str = None,
        by_channel_search_string: str = None,
    ):
        if by_url:
            url = by_url
        elif by_channel_id:
            url = yt_channel_id_to_url(by_channel_id)
        elif by_channel_search_string:
            req = logged_get(
                url=YT_BASE_API_SEARCH_URL,
                q=by_channel_search_string,
                key=YT_API_KEY,
                part="snippet",
                type="channel",
            )

            channel_id = req.json()["items"][0]["id"]["channelId"]
            url = yt_channel_id_to_url(channel_id)
        else:
            raise Exception("You need to specify at least on param")

        super().__init__(url=url)

    @property
    def id(self):
        r = r"(?<=channel\/)([A-z]|[0-9])+"
        return re.search(r, self.url).group()

    # --- Iterator related funcs ---

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
            _params.update({ApiFieldsEnum.PAGE_TOKEN: page_token})

        if self._published_after_param and self.SUPPORT_FILTER_BY_DATE:
            _params.update(
                {
                    ApiFieldsEnum.PUBLISHED_AFTER: yt_datetime_to_str_param(
                        self._published_after_param
                    )
                }
            )

        req = logged_get(YT_BASE_API_SEARCH_URL, _params)

        if req.status_code == 200:
            json = req.json()
            json_items = json.get("items")

            self.next_page_token = json.get(ApiFieldsEnum.NEXT_PAGE_TOKEN, None)
            self.q.extend(json_items)
        elif req.status_code == 403:  # Forbidden
            raise Exception(f"=== YT API FORBIDDEN ===")

    def next(self) -> Optional["ItemDataclassClass"]:
        if len(self.q) > 0:
            head_elem = self.q.pop(0)
            dataclass_item = self.ItemDataclassClass.from_raw_data(head_elem)

            return (
                dataclass_item if dataclass_item else self.next()
            )  # TODO Move __next__to common ApiChannel
        elif self.next_page_token is None:
            self.next_page_token = ""
            self._published_after_param = None
            raise StopIteration
        else:
            self.fetch_next_page(self.next_page_token)
            return self.next()


class YTApiVideo(ApiItem):
    ItemDataclassClass = YTVideoDataclass

    def __init__(self, video_id: str):
        self.id = video_id

        url = yt_id_to_url(video_id)
        super().__init__(url=url)

        self.fetch_data()

    def fetch_data(self):
        _params = {
            "key": YT_API_KEY,
            "id": self.id,
            "part": "snippet",
        }

        req = logged_get(YT_BASE_API_VIDEOS_URL, _params)

        self.item_object = self.ItemDataclassClass.from_raw_data(req.json())


class YTVideo:
    ApiItemClass: Type[ApiItem] = YTApiVideo
