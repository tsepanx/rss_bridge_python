import os
import random
from typing import Sequence

import magic
from feedgen.feed import FeedGenerator

from src.base import ApiChannel, Item
from src.tg_api import TGApiChannel
from src.utils import (
    DEFAULT_RSS_FORMAT,
    RUN_IDENTIFIER,
    SRC_PATH,
    TG_RSS_USE_HTML,
    RssFormat,
    logged_get,
)
from src.yt_api import YTApiChannel


def channel_gen_rss(
    channel: ApiChannel,
    items: Sequence[Item],
    rss_format: RssFormat | None = DEFAULT_RSS_FORMAT,
    use_enclosures: bool | None = False,
):
    channel_username = (
        channel.username
        if channel.username
        else "unknown" + str(random.randint(0, 1000))
    )

    title_indent_size = 22
    title_indent_string = " " * (
        title_indent_size - (min(title_indent_size, len(channel_username)))
    )
    if isinstance(channel, TGApiChannel):
        title_prefix = "TELEGRAM"
    elif isinstance(channel, YTApiChannel):
        title_prefix = "YOUTUBE"
    else:
        raise Exception("Unknown channel class")

    feed_title = f"{title_prefix} {RUN_IDENTIFIER} | {channel_username}{title_indent_string}| {channel.full_name}"
    feed_url = channel.url
    feed_desc = channel.description

    fg = FeedGenerator()

    fg.id(feed_url)
    fg.title(feed_title)
    fg.author({"name": feed_title, "uri": feed_url})
    fg.link(href=feed_url, rel="alternate")
    fg.logo(channel.logo_url)
    if feed_desc:
        fg.subtitle(feed_desc)

    for i in reversed(items):
        link = i.url

        if i.html_content and TG_RSS_USE_HTML:
            content = i.html_content
            content_type = "html"
        elif i.text_content:
            content = i.text_content
            content_type = None
        else:
            raise Exception(f"Item {i} has no appropriate content")

        fe = fg.add_entry()
        fe.id(i.url)
        fe.title(i.title)
        fe.published(i.pub_date)
        fe.content(content, type=content_type)
        fe.link(href=link)

        if use_enclosures and i.preview_img_url:
            media_bytes = logged_get(i.preview_img_url).content

            enclosure_type = magic.from_buffer(media_bytes, mime=True)
            enclosure_len = len(media_bytes)

            fe.link(
                href=i.preview_img_url,
                rel="enclosure",
                type=enclosure_type,
                length=str(enclosure_len),
            )

    dirname = os.path.join(SRC_PATH, "feeds")
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    dirname = os.path.join(dirname, channel_username)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    if rss_format is RssFormat.RSS:
        path = f"{dirname}/rss.xml"
        func = fg.rss_file
    elif rss_format is RssFormat.ATOM:
        path = f"{dirname}/atom.xml"
        func = fg.atom_file
    else:
        raise Exception("No rss_format specified")

    func(path, pretty=True)
    return path
