import pprint
import re
from typing import List
import dataclasses

from yt_api import last_channel_videos


@dataclasses.dataclass
class ContentItem:
    """
    Base interface defining Feed.fetch() return type
    """

    url: str = None
    title: str = None
    pic_url: str = None


class Feed:
    ContentItemType = ContentItem

    def __init__(self, url=None):
        self.url = url

    def fetch(self) -> List[ContentItem]:
        """
        Base function to get new updates from given feed.
        Must be overridden by every Sub-class.
        :return: List[ContentItem]
        """
        pass


class YTContentItem(ContentItem):
    def __init__(self, d: dict):  # Init by json item from YT API
        try:
            video_id = d['id']['videoId']
            title = d['snippet']['title']

            video_url = f'https://www.youtube.com/watch?v={video_id}'
            video_pic_url = d['snippet']['thumbnails']['medium']['url']

            super().__init__(
                url=video_url,
                title=title,
                pic_url=video_pic_url
            )
        except Exception:
            print(f'Error for parsing video data')


class YTFeed(Feed):
    ContentItemType = YTContentItem

    def __init__(self, channel_url=None, channel_id=None):
        if channel_url:
            super().__init__(url=channel_url)
        elif channel_url:
            super().__init__(url=f'https://youtube.com/channel/{channel_id}')

    @property
    def id(self):
        r = '(?<=channel\/)([A-z]|[0-9])+'
        return re.search(r, self.url).group()

    def api_result_item_to_dataclass(self, d: dict) -> ContentItemType: pass  # TODO

    def fetch(self) -> List[ContentItemType]:
        cur_fetched = last_channel_videos(self.id, count=10)

        # new_list = cur_fetched - last_fetched_list # TODO Compare with previously fetched list from db

        return [YTContentItem(i) for i in cur_fetched]


if __name__ == "__main__":
    yt1 = YTFeed(channel_url="https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg")

    pprint.pprint(yt1.fetch())
