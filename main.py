import datetime
import os
from typing import List

from feedgen.feed import FeedGenerator

from tg_api import TGPostDataclass, TGApiChannel
from utils import shortened_text, Feed
from yt_api import YTVideoDataclass, YTApiChannel


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

    def __init__(self, tg_alias: str):
        super().__init__(f'https://t.me/s/{tg_alias}')


def gen_rss(feed: Feed, after_date: datetime.date = None):
    fg = FeedGenerator()

    items: List[TGPostDataclass] = feed.fetch_all(after_date=after_date)

    fg.id(feed.url)
    fg.title(f'TG Channel feed [TEST] {feed.api_object.channel_name}')
    fg.author({'name': 'feed-aggregator', 'uri': 'https://github.com/tsepanx/feed-aggregator'})
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
        fe.id(i.url)
        fe.title(shortened_text(i.text))
        fe.content(i.text)
        fe.link(href=i.url)
        if i.preview_img_url:
            fe.link(
                href=i.preview_img_url,
                rel='enclosure',
                type=f"media/{i.preview_img_url[i.preview_img_url.rfind('.') + 1:]}"
            )
        fe.published(dt)

    dirname = f'feeds/{feed.api_object.channel_name}'
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    fg.atom_file(f'{dirname}/atom.xml')  # Write the ATOM feed to a file
    fg.rss_file(f'{dirname}/rss.xml')  # Write the RSS feed to a file


if __name__ == "__main__":
    week_delta = datetime.timedelta(days=7)
    last_n_weeks = lambda n: datetime.date.today() - n * week_delta

    gen_rss(
        # TGFeed('notboring_tech'),
        TGFeed('black_triangle_tg'),
        after_date=last_n_weeks(1)
    )
