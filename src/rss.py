import os
from typing import Optional, Sequence

import magic
from feedgen.feed import FeedGenerator

from src.base import ApiChannel, ItemDataclass
from src.tg_api import TGApiChannel
from src.utils import RUN_IDENTIFIER, SRC_PATH, RssFormat, logged_get


def channel_gen_rss(
    channel: ApiChannel,
    items: Sequence[ItemDataclass],
    rss_format: Optional[RssFormat] = RssFormat.Atom,
    use_enclosures: Optional[bool] = False,
):
    title_indent_size = 22
    title_indent_string = " " * (
        title_indent_size - (min(title_indent_size, len(channel.username)))
    )
    title_prefix = "TELEGRAM" if isinstance(channel, TGApiChannel) else "YOUTUBE"

    feed_title = f"{title_prefix} {RUN_IDENTIFIER} | {channel.username}{title_indent_string}| {channel.full_name}"
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

        if i.html_content:
            content = i.html_content
            content_type = "html"
        elif i.text_content:
            content = i.text_content
            content_type = None
        else:
            raise Exception(f"ApiChannel {channel.url} has no text_content")

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

    dirname = os.path.join(dirname, channel.username)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    if rss_format is RssFormat.Rss:
        path = f"{dirname}/rss.xml"
        func = fg.rss_file
    elif rss_format is RssFormat.Atom:
        path = f"{dirname}/atom.xml"
        func = fg.atom_file
    else:
        raise Exception("No rss_format specified")

    func(path, pretty=True)
    return path
