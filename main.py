import pprint
import re
from typing import List
import dataclasses

from tg_api import TGPostDataclass, TGApiChannel
from utils import ContentItem, ApiClass
from yt_api import YTVideoDataclass, YTApiChannel


class Feed:
    ContentItemClass = ContentItem
    api_class: ApiClass = ApiClass

    def __init__(self, url: str):
        self.url = url
        self.api_object = self.api_class(url)

    def fetch(self) -> List[ContentItemClass]:
        """
        Base function to get new updates from given feed.
        Must be overridden by every Sub-class.
        :return: List[ContentItem]
        """

        content_items = list(self.api_object)  # TODO Fetch not all available items
        return content_items


class YTFeed(Feed):
    ContentItemClass = YTVideoDataclass
    api_class = YTApiChannel

    def __init__(self, channel_url=None, channel_id=None):
        if channel_url:
            super().__init__(url=channel_url)
        elif channel_url:
            super().__init__(url=f'https://youtube.com/channel/{channel_id}')

class TGFeed(Feed):
    ContentItemClass = TGPostDataclass
    api_class = TGApiChannel


if __name__ == "__main__":
    yt1 = YTFeed(channel_url="https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg")
    tg1 = TGFeed('https://t.me/s/prostyemisli')

    pprint.pprint(tg1.fetch())
    pprint.pprint(yt1.fetch())
