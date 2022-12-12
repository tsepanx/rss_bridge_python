import dataclasses
import re
from typing import List, Optional

import fastapi
from fastapi import HTTPException

from .base import ApiChannel, ApiItem, Item
from .utils import (
    YT_API_KEY,
    YT_API_MAX_RESULTS_PER_PAGE,
    YT_BASE_API_SEARCH_URL,
    YT_BASE_API_VIDEOS_URL,
    is_youtube_channel_id,
    is_youtube_link,
    logged_get,
    shortened_text,
    yt_channel_id_to_url,
    yt_datetime_to_str_param,
    yt_id_to_url,
    yt_str_param_to_datetime,
)


@dataclasses.dataclass
class YTVideo(Item):
    @classmethod
    def from_raw_data(cls, json: dict) -> Optional["YTVideo"]:
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
            preview_media_url=preview_img_url,
        )

    def __repr__(self):
        return f"{self.url} | {shortened_text(self.title, 30)} | {self.pub_date}"


class ApiFieldsEnum:
    PAGE_TOKEN = "pageToken"
    NEXT_PAGE_TOKEN = "nextPageToken"
    PUBLISHED_AFTER = "publishedAfter"


class YTApiChannel(ApiChannel):
    ItemClass: type[Item] = YTVideo

    SUPPORT_FILTER_BY_DATE = True
    q: List[dict] = list()
    next_page_token: str = ""
    metadata_search_string = None

    def __init__(self, s: str):
        self.metadata_search_string = s

        if is_youtube_link(s):
            _url = s
        elif is_youtube_channel_id(s):
            _url = yt_channel_id_to_url(s)
        else:
            # url will be fetched as metadata
            _url = None

        super().__init__(url=_url)

    @property
    def id(self):
        if not self.url:
            return None
        return re.search(r"(?<=channel/)([A-z]|[0-9])+", self.url).group()

    @id.setter
    def id(self, value):
        self.url = "https://www.youtube.com/channel/" + value

    @property
    def username(self):
        return self.full_name

    def is_fetched_metadata(self):
        return self.username is not None  # TODO Check for existing data from DB

    def fetch_metadata(self):
        super().fetch_metadata()

        if not self.metadata_search_string:
            raise Exception("No string for metadata search is given")

        req = logged_get(
            url=YT_BASE_API_SEARCH_URL,
            params={
                "q": self.metadata_search_string,
                "key": YT_API_KEY,
                "part": "snippet",
                "type": "channel",
            },
        )

        items = req.json()["items"]
        if len(items) == 0:
            raise HTTPException(
                fastapi.status.HTTP_404_NOT_FOUND,
                f"Youtube API: Channel search failed for given string: '{self.metadata_search_string}'",
            )

        channel_json = items[0]

        self.id = channel_json["id"]["channelId"]  # self.url setter
        self.full_name = channel_json["snippet"]["title"]
        self.description = channel_json["snippet"]["description"]
        self.logo_url = channel_json["snippet"]["thumbnails"]["default"]["url"]

    # --- Iterator related funcs ---
    def reset_fetch_fields(self):
        super().reset_fetch_fields()
        self.next_page_token = ""
        self._published_after_param = None

    def fetch_next_page(self, page_token: str | None = None):
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
            msg = req.json()["error"]["message"]
            raise Exception(f"=== YT API FORBIDDEN === | {msg}")

    def fetch_next(self):
        return self.fetch_next_page(self.next_page_token)

    def is_iteration_ended(self):
        return self.next_page_token is None


class YTApiVideo(ApiItem):
    ItemClass = YTVideo

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

        self.item_object = self.ItemDataclassClass.from_raw_data(
            req.json()
        )  # TODO What?
