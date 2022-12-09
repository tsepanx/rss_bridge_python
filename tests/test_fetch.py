import datetime
from typing import Sequence

import feedparser  # type: ignore  # noqa
import pytest

from src.base import ApiChannel, Item
from src.rss import channel_gen_rss
from src.tg_api import TGApiChannel
from src.utils import DEFAULT_TZ, RssFormat, struct_time_to_datetime
from src.yt_api import YTApiChannel


def gen_rss_check(
    channel: ApiChannel,
    items: Sequence[Item],
    rss_format: RssFormat,
    expected_content_type: str = "text/html",
):
    path = channel_gen_rss(
        channel,
        items,
        rss_format=rss_format,
        # use_enclosures=True
    )
    assert path.endswith(".xml")

    # --- Parse file ---

    parsed = feedparser.parse(path)
    assert len(parsed.entries) == len(items)

    prev_item_pub_date = datetime.datetime.max
    for i in parsed.entries:
        i_published = struct_time_to_datetime(i.published_parsed)
        assert i.id is not None
        assert i.title is not None
        assert i_published <= prev_item_pub_date  # Dates are in descending order
        if rss_format is RssFormat.ATOM:
            assert i.content[0].type == expected_content_type

        prev_item_pub_date = i_published


@pytest.mark.parametrize("alias", ["black_triangle_tg", "ontol", "prostyemisli"])
@pytest.mark.parametrize(
    "rss_format",
    [RssFormat.ATOM, RssFormat.RSS],
)
@pytest.mark.dependency()
def test_tg_channel_fetch(alias, rss_format):
    tg_channel = TGApiChannel(alias)
    posts_list = tg_channel.fetch_items()

    # --- Test fetch_items() ordered by date ---

    assert len(posts_list) <= 20

    prev_item_pub_date = datetime.datetime.max.replace(tzinfo=DEFAULT_TZ)
    for p in posts_list:
        assert p.pub_date < prev_item_pub_date

    # --- RSS Generation ---

    gen_rss_check(tg_channel, posts_list, rss_format)


@pytest.mark.parametrize(
    "channel_url",
    ["https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg", "distrotube"],
)
@pytest.mark.parametrize(
    "published_after", [datetime.datetime(2022, 9, 15, tzinfo=DEFAULT_TZ)]
)
@pytest.mark.parametrize(
    "rss_format",
    [RssFormat.ATOM],
)
def test_yt_channel_fetch(channel_url, published_after, rss_format):
    yt_channel = YTApiChannel(channel_url)

    # --- Test filtered by date ---

    videos_list = yt_channel.fetch_items(after_date=published_after)

    for v in videos_list:
        assert v.pub_date >= published_after

    # --- Test filtered by count ---

    n = 10
    videos_list2 = yt_channel.fetch_items(entries_count=n)
    assert len(videos_list2) == n

    # --- RSS Generation ---

    gen_rss_check(
        yt_channel, videos_list, rss_format, expected_content_type="text/plain"
    )
