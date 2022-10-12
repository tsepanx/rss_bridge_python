import datetime

import feedparser
import pytest

from src.rss import channel_gen_rss
from src.tg_api import TGApiChannel
from src.utils import DEFAULT_TZ, RssFormat, struct_time_to_datetime
from src.yt_api import YTApiChannel


@pytest.mark.parametrize("alias", ["black_triangle_tg", "ontol", "prostyemisli"])
@pytest.mark.parametrize(
    "with_enclosures",
    [
        # True,
        False
    ],
)
@pytest.mark.dependency()
def test_tg_channel_fetch(alias, with_enclosures):
    tg_channel = TGApiChannel(alias)
    posts_list = tg_channel.fetch_items()

    assert len(posts_list) <= 20

    prev_item_pub_date = datetime.datetime.max.replace(tzinfo=DEFAULT_TZ)
    for p in posts_list:
        assert p.pub_date < prev_item_pub_date

    path = channel_gen_rss(
        tg_channel,
        posts_list,
        rss_format=RssFormat.Atom,
        use_enclosures=with_enclosures,
    )
    assert path.endswith(".xml")

    parsed = feedparser.parse(path)
    assert len(parsed.entries) == len(posts_list)

    prev_item_pub_date = datetime.datetime.max
    for i in parsed.entries:
        i_published = struct_time_to_datetime(i.published_parsed)
        assert i.id is not None
        assert i.title is not None
        assert i_published <= prev_item_pub_date  # Dates are in descending order
        assert i.content[0].type == "text/html"

        prev_item_pub_date = i_published


@pytest.mark.parametrize(
    "channel_url", ["https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg"]
)
@pytest.mark.parametrize(
    "published_after", [datetime.datetime(2022, 9, 15, tzinfo=DEFAULT_TZ)]
)
def test_yt_channel_fetch(channel_url, published_after):
    yt_channel = YTApiChannel(channel_url)

    # --- Filter by date ---

    videos_list = yt_channel.fetch_items(after_date=published_after)

    for v in videos_list:
        assert v.pub_date >= published_after

    # --- Filter by count ---

    n = 10
    videos_list2 = yt_channel.fetch_items(entries_count=n)
    assert len(videos_list2) == n
