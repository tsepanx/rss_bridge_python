import datetime
import pprint
from random import randint
from typing import List, Type

from feedgen.feed import FeedGenerator

from tg_api import TGPostDataclass, TGApiChannel
from utils import ContentItem, ApiClass
from yt_api import YTVideoDataclass, YTApiChannel


class Feed:
    ContentItemClass = ContentItem
    api_class: Type[ApiClass] = ApiClass

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

        return list(self.api_object)  # Invokes generator with http requests

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


def gen_rss(feed: Feed, after_date: datetime.date = None) -> str:
    fg = FeedGenerator()

    items = feed.fetch_all(after_date=after_date)

    fg.id(feed.url)
    fg.title(f'TG Channel feed [TEST] {feed.api_object.channel_name}')
    fg.author({'name': 'Stepan Tsepa', 'uri': 'https://github.com/tsepanx'})
    fg.link(href=feed.url, rel='alternate')
    fg.logo(feed.api_object.channel_img_url)
    # fg.subtitle('_Subtitle_')
    fg.subtitle(feed.api_object.channel_desc)
    # fg.link(href='https://larskiesow.de/test.atom', rel='self')
    # fg.language('en')

    for i in items:
        dt = datetime.datetime.combine(
            i.pub_date,
            datetime.time.min,
            datetime.timezone.utc
        )

        fe = fg.add_entry()
        fe.id('ID')
        fe.title('TITLE 2')
        fe.description('DESC')
        fe.content('CONTENT')
        fe.link(link='LINK')
        fe.author({'name': 'AUTHOR NAME', 'uri': 'AUTHOR URI'})
        # fe.category('CATEGORY')
        fe.source('SOURCE')
        fe.summary('SUMMARY')
        fe.guid(f'GUID {randint(1, 100)}')
        fe.published(dt)

        # fe = fg.add_entry()
        # fe.id(i.url)
        # fe.title(i.title)
        # # fe.description(i.text)
        # fe.content(i.text)
        # fe.link(href=i.url)
        # fe.pubDate(dt)

    # atomfeed = fg.atom_str(pretty=True)  # Get the ATOM feed as string
    # rssfeed = fg.rss_str(pretty=True)  # Get the RSS feed as string
    # fg.atom_file('atom.xml')  # Write the ATOM feed to a file
    # fg.rss_file('rss.xml')  # Write the RSS feed to a file

    return fg.rss_file('rss.xml')  #datetime.datetime.combine(i.pub_date, datetime.time.min) Write the RSS feed to a file


if __name__ == "__main__":
    yt1 = YTFeed("https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg")
    tg_prostye = TGFeed('https://t.me/s/prostyemisli')

    week_delta = datetime.timedelta(days=7)
    last_n_weeks = lambda n: datetime.date.today() - n * week_delta

    gen_rss(
        tg_prostye,
        after_date=last_n_weeks(2)
    )

    # pprint.pprint(
    #     tg1.fetch_all(after_date=last_n_weeks(2))
    # )
    # pprint.pprint(yt1.fetch_all())

