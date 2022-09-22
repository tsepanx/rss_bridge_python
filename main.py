import datetime
import pprint
from typing import List

from tg_api import TGPostDataclass, TGApiChannel
from utils import ContentItem, ApiClass
from yt_api import YTVideoDataclass, YTApiChannel


class Feed:
    ContentItemClass = ContentItem
    api_class: ApiClass = ApiClass

    def __init__(self, url: str):
        self.url = url
        self.api_object = self.api_class(url)

    def fetch_all(self, after_date: datetime.date = None) -> List[ContentItem]:
        """
        Base function to get new updates from given feed.
        Must be overridden by every Sub-class.
        :return: List[ContentItem]
        """
        if after_date:
            if self.api_class.SUPPORT_FILTER_BY_DATE:
                self.api_object.published_after_param = after_date
            else:
                result = list()
                try:
                    for i in iter(self.api_object):
                        if i.pub_date > after_date:
                            result.append(i)
                        else:
                            raise StopIteration
                except StopIteration:
                    return result

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
    yt1 = YTFeed("https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg")
    tg1 = TGFeed('https://t.me/s/prostyemisli')

    week_delta = datetime.timedelta(days=7)
    last_n_weeks = lambda n: datetime.date.today() - n * week_delta

    pprint.pprint(
        tg1.fetch_all(after_date=last_n_weeks(2))
    )
    # pprint.pprint(yt1.fetch_all())
