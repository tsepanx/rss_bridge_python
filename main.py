from typing import List
import dataclasses


@dataclasses.dataclass
class ContentItem:
    """
    Base interface defining feed.fetch() return type
    """

    title: str = None
    url: str = None
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


class YTContentItem(ContentItem): pass


class YTFeed(Feed):
    ContentItemType = YTContentItem

    def __init__(self, channel_url=None, channel_id=None):
        if channel_url:
            super().__init__(url=channel_url)
        elif channel_url:
            super().__init__(url=f'https://youtube.com/c/{channel_id}')

    def api_result_item_to_dataclass(self, d: dict) -> ContentItemType: pass  # TODO

    def fetch(self) -> List[ContentItemType]:
        # last_fetched_list = []
        # cur_fetched = [] # TODO Run some youtube api
        # new_list = cur_fetched - last_fetched_list
        # return [self.api_result_item_to_dataclass(i) for i in new_list]
        pass
