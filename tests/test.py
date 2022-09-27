import datetime
import feedparser

from src.tg_api import TGFeed, tg_gen_rss
from src.utils import RssFormat, struct_time_to_datetime
from src.yt_api import YTFeed
import pytest

@pytest.mark.parametrize('alias', [
    'black_triangle_tg',
    'ontol',
    'prostyemisli'
])
@pytest.mark.parametrize('with_enclosures', [
    # True,
    False
])
def test_tg_channel_fetch(alias, with_enclosures):
    tg_feed = TGFeed(alias)
    tg_fetched_list = tg_feed.fetch()

    assert len(tg_fetched_list) > 0

    path = tg_gen_rss(
        tg_feed,
        tg_fetched_list,
        rss_format=RssFormat.Atom,
        use_enclosures=with_enclosures
    )
    assert path.endswith('.xml')

    parsed = feedparser.parse(path)
    assert len(parsed.entries) == len(tg_fetched_list)

    prev_item_pub_date = datetime.datetime.max
    for i in parsed.entries:
        i_published = struct_time_to_datetime(i.published_parsed)
        assert i.id is not None
        assert i.title is not None
        assert i_published <= prev_item_pub_date  # Dates are in descending order

        prev_item_pub_date = i_published


@pytest.mark.parametrize('channel_url', [
    "https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg"
])
@pytest.mark.parametrize('published_after', [
    datetime.datetime(2022, 9, 15)
])
def test_yt_channel_fetch(channel_url, published_after):
    feed = YTFeed(channel_url)

    # --- Filter by date ---

    videos_list = feed.fetch(
        after_date=published_after
    )

    for v in videos_list:
        assert v.pub_date >= published_after

    # --- Filter by count ---

    n = 10
    videos_list2 = feed.fetch(entries_count=n)
    assert len(videos_list2) == n
