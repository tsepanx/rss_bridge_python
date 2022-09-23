import datetime
import os
import pprint
from typing import List, Type, TypeVar

from feedgen.feed import FeedGenerator

from tg_api import TGPostDataclass, TGApiChannel
from utils import shortened_text, Feed, ContentItem
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


def gen_rss(
        items: List[Type[ContentItem]],
        feed_url: str,
        feed_title: str,
        feed_desc: str = None):
    fg = FeedGenerator()

    fg.id(feed_url)
    fg.title(f'TG | {feed_title}')
    fg.author({'name': feed_title, 'uri': feed_url})
    fg.link(href=feed_url, rel='alternate')
    # fg.logo(feed.api_object.channel_img_url)
    if feed_desc:
        fg.subtitle(feed_desc)
    # fg.link(href='https://larskiesow.de/test.atom', rel='self')
    # fg.language('en')

    for i in items:
        dt = datetime.datetime.combine(
            i.pub_date,
            datetime.time.min,
            datetime.timezone.utc
        )

        if isinstance(i, TGPostDataclass):  # Make tg preview link as rss item link
            link = i.preview_link_url if i.preview_link_url else i.url
        else:
            link = i.url

        content = i.html_content if i.html_content else i.text

        fe = fg.add_entry()
        fe.id(i.url)
        fe.title(shortened_text(i.text, 50))
        fe.content(content)
        fe.link(href=link)
        if i.preview_img_url:
            fe.link(
                href=i.preview_img_url,
                rel='enclosure',
                type=f"media/{i.preview_img_url[i.preview_img_url.rfind('.') + 1:]}"
            )
        fe.published(dt)

    dirname = f'feeds/{feed_title.replace(" ", "_")}'
    if not os.path.exists('feeds'):
        os.mkdir('feeds')

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    fg.atom_file(f'{dirname}/atom.xml')  # Write the ATOM feed to a file
    fg.rss_file(f'{dirname}/rss.xml')  # Write the RSS feed to a file


week_delta = datetime.timedelta(days=7)
last_n_weeks = lambda n: datetime.date.today() - n * week_delta

# if __name__ == "__main__":
#     tg_alias = 'black_triangle_tg'
#     feed = TGFeed(tg_alias)
#     feed.fetch_all(
#         last_n_weeks(1)
#     )

if __name__ == "__main__":
    aliases = list(
        filter(
            lambda x: not x.startswith('#'),
            map(
                str.strip,
                open('tg_aliases').readlines()
            )
        )
    )

    for i in aliases:
        f = TGFeed(i)
        items = f.fetch_all(after_date=last_n_weeks(1))

        gen_rss(items,
                feed_url=f.url,
                feed_title=f.api_object.channel_name,
                feed_desc=f.api_object.channel_desc)
