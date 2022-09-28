import datetime
import os
import re
import bs4
import magic
from dataclasses import dataclass
from typing import Optional, List, Sequence
from feedgen.feed import FeedGenerator

from .utils import shortened_text, logged_get, TG_BASE_URL, RssFormat, \
    TG_COMBINE_HTML_WITH_PREVIEW, TG_RSS_USE_HTML, RUN_IDENTIFIER, DEFAULT_TZ
from .base import ItemDataclass, ApiChannel, ItemDataclassType


@dataclass
class TGPostDataclass(ItemDataclass):
    preview_link_url: Optional[str] = None

    @classmethod
    def from_raw_data(cls, data: bs4.element.Tag) -> Optional['TGPostDataclass']:
        """
        :param data: bs4 Tag element that is wrapper of single TG channel message
        """
        post = data

        href_date_tag = post.findChild(name='a', attrs={'class': 'tgme_widget_message_date'})
        datetime_str = href_date_tag.contents[0].get('datetime')
        post_date = datetime.datetime.fromisoformat(
            datetime_str
        ).replace(tzinfo=DEFAULT_TZ)  # Convert from string to pythonic format

        post_href = href_date_tag.get('href')

        text_wrapper = post.findChild(name='div', attrs={'class': 'tgme_widget_message_text'})
        if not text_wrapper:
            return None
        text = text_wrapper.get_text('\n', strip=True)
        html_content = str(text_wrapper)

        link_preview_wrapper = post.findChild(name='a', attrs={'class': 'tgme_widget_message_link_preview'})

        if link_preview_wrapper:  # There is a preview section
            link_preview_url = link_preview_wrapper.get('href')

            link_preview_img_tag = post.findChild(name='i', attrs={'class': 'link_preview_right_image'}) or \
                                   post.findChild(name='i', attrs={'class': 'link_preview_image'}) or \
                                   post.findChild(name='i', attrs={'class': 'link_preview_video_thumb'})

            if link_preview_img_tag:
                link_preview_img_tag_style = link_preview_img_tag.get('style')
                r = r"background-image:url\('(.*)'\)"
                link_preview_img = re.findall(r, link_preview_img_tag_style)[0]
            else:
                link_preview_img = None

            link_preview_title = link_preview_wrapper.find(attrs={'class': 'link_preview_title'})
            link_preview_desc = link_preview_wrapper.find(attrs={'class': 'link_preview_description'})

            if TG_COMBINE_HTML_WITH_PREVIEW:
                html_content += f'<br/>Preview content:<br/>{link_preview_title}<br/>{link_preview_desc}'
        else:
            link_preview_url = None
            link_preview_img = None
            link_preview_title = None
            link_preview_desc = None

        title = shortened_text(text, 50)

        return cls(
            pub_date=post_date,
            url=post_href,
            title=title,
            text_content=text,
            html_content=html_content,
            preview_link_url=link_preview_url,
            preview_img_url=link_preview_img,
        )

    def __repr__(self):
        return f'{self.url} | {self.title} | {self.pub_date} | {self.preview_link_url}'


class TGApiChannel(ApiChannel):
    """
    Basic api related class representing single telegram channel
    iter(TGApiChannel) iterates over its channel messages (posts) ordered by pub date
    """
    ItemDataclassClass: ItemDataclassType = TGPostDataclass

    SUPPORT_FILTER_BY_DATE = False
    q: List[bs4.element.Tag] = list()
    next_url: Optional[str] = None

    def __init__(self, url_or_alias: str):
        channel_username = re.search('[^/]+(?=/$|$)', url_or_alias).group()

        self.username = channel_username or url_or_alias
        url = f'https://t.me/s/{channel_username}'

        self.next_url = url  # TODO make it common in ApiChannel
        super().__init__(url=url)

    def fetch_metadata(self):
        print('\nMETADATA | ', end='')
        req = logged_get(self.url)
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        # --- Parse channel title ---
        channel_metadata_wrapper = soup.find(
            name='div', attrs={'class': 'tgme_channel_info_header'},
            recursive=True
        )

        channel_title = channel_metadata_wrapper.findChild(name='span').contents[0]

        channel_img_url = channel_metadata_wrapper.findChild(name='img', recursive=True)
        channel_img_url = channel_img_url.get('src')

        channel_desc = soup.findChild(
            name='div', attrs={
                'class': 'tgme_channel_info_description'
            },
            recursive=True
        ).contents[0]

        self.username = str(channel_title)
        self.logo_url = channel_img_url
        self.description = str(channel_desc)

    # --- Iterator related funcs ---
    # @lru_cache
    # @limit_requests(count=1)  # TODO Limit fetch_items count if no attr applied
    def on_fetch_new_chunk(self, fetch_url: str):  # -> Optional[str]:
        """
        :param fetch_url: Link to previous channel posts.
        example: https://t.me/s/notboring_tech?before=2422

        :return: Next fetch_url for fetching next page of posts
        """
        print(f'TG: NEW CHUNK | ', end='')
        req = logged_get(fetch_url)
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        # --- Get list of posts wrappers
        posts_list = soup.findChildren(
            name='div', attrs={'class': 'tgme_widget_message_wrap'},
            recursive=True
        )

        self.q.extend(reversed(posts_list))  # TODO convert to dataclass on the fly

        # --- Next messages page href parsing
        messages_more_tag = soup.find(
            name='a', attrs={'class': 'tme_messages_more'},
            recursive=True
        )

        if not messages_more_tag:
            print('Retrying fetch_items...')
            self.on_fetch_new_chunk(fetch_url)  # Try to fetch_items again

        if messages_more_tag.get('data-after'):  # We reached end of posts list
            self.next_url = None
        else:
            next_page_href = messages_more_tag.get('href')
            next_page_link = f'{TG_BASE_URL}{next_page_href}'

            self.next_url = next_page_link

    def next(self) -> ItemDataclassClass:  # TODO Maybe change this method
        if len(self.q) > 0:
            head_post = self.q.pop(0)
            dataclass_item = self.ItemDataclassClass.from_raw_data(head_post)

            return dataclass_item if dataclass_item else self.next()
        elif not self.next_url:
            raise StopIteration
        else:  # No left fetched posts in queue
            self.on_fetch_new_chunk(self.next_url)
            return self.next()


def tg_gen_rss(
        channel: TGApiChannel,
        items: Sequence[TGPostDataclass],
        rss_format: RssFormat = RssFormat.Atom,
        use_enclosures: bool = False
):

    feed_url = channel.url

    indent_size = 22
    indent_str = " " * (indent_size - (min(indent_size, len(channel.username))))

    feed_title = f'TG {RUN_IDENTIFIER} | {channel.username}{indent_str}| {channel.username}'
    feed_desc = channel.description

    fg = FeedGenerator()

    fg.id(feed_url)
    fg.title(feed_title)
    fg.author({'name': feed_title, 'uri': feed_url})
    fg.link(href=feed_url, rel='alternate')
    fg.logo(channel.logo_url)
    if feed_desc:
        fg.subtitle(feed_desc)

    for i in reversed(items):
        link = i.url

        if TG_RSS_USE_HTML and i.html_content:
            content = i.html_content
            content_type = 'html'
        else:
            content = i.text_content
            content_type = None

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
                rel='enclosure',
                type=enclosure_type,
                length=str(enclosure_len)
            )

    dirname = f'feeds'
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    dirname = os.path.join(dirname, channel.username)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    if rss_format is RssFormat.Rss:
        path = f'{dirname}/rss.xml'
        func = fg.rss_file
    elif rss_format is RssFormat.Atom:
        path = f'{dirname}/atom.xml'
        func = fg.atom_file
    else: raise Exception('No rss_format specified')

    func(path, pretty=True)
    return path
