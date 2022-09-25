import datetime
import os
import re
import bs4
from dataclasses import dataclass
from typing import Optional, List, Sequence
from feedgen.feed import FeedGenerator

from utils import shortened_text, logged_get, TG_BASE_URL, RssFormat, TG_COMBINE_HTML_WITH_PREVIEW, TG_RSS_USE_HTML, RUN_IDENTIFIER
from base import ContentItem, ApiClass, Feed


@dataclass
class TGPostDataclass(ContentItem):
    preview_link_url: Optional[str] = None

    def __repr__(self):
        return f'{self.url} | {shortened_text(self.text, 50)} | {self.pub_date} | {self.preview_link_url}'


class TGApiChannel(ApiClass):
    """
    Basic api related class representing single telegram channel
    iter(TGApiChannel) iterates over its channel messages (posts) ordered by pub date
    """
    SUPPORT_FILTER_BY_DATE = False
    q: List[bs4.element.Tag] = list()
    next_url: Optional[str] = None

    def __init__(self, url: str):
        print(f'init with {url}')
        self.next_url = url

        super().__init__(
            url=url
        )

    def fetch_channel_metadata(self):
        req = logged_get(self.url)
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        # --- Parse channel title ---
        channel_metadata_wrapper = soup.find(
            name='div', attrs={
                'class': 'tgme_channel_info_header'},
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

        self.channel_name = str(channel_title)
        self.channel_img_url = channel_img_url
        self.channel_desc = str(channel_desc)

    # --- Iterator related funcs ---
    # @lru_cache
    def fetch_next_posts_page(self, fetch_url: str):  # -> Optional[str]:
        """
        :param fetch_url: Link to fetch_all previous channel posts.
        example: https://t.me/s/notboring_tech?before=2422

        :return: Next fetch_url for fetching next page of posts
        """
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
            print('Retrying fetch...')
            self.fetch_next_posts_page(fetch_url)  # Try to fetch again

        if messages_more_tag.get('data-after'):  # We reached end of posts list
            self.next_url = None
        else:
            next_page_href = messages_more_tag.get('href')
            next_page_link = f'{TG_BASE_URL}{next_page_href}'

            self.next_url = next_page_link

    @staticmethod
    def html_tag_to_dataclass(post: bs4.element.Tag) -> Optional[TGPostDataclass]:
        href_date_tag = post.findChild(name='a', attrs={'class': 'tgme_widget_message_date'})
        datetime_str = href_date_tag.contents[0].get('datetime')
        post_date = datetime.datetime.fromisoformat(datetime_str)  # Convert from string to pythonic format

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

        return TGPostDataclass(
            pub_date=post_date,
            url=post_href,
            text=text,
            html_content=html_content,
            preview_link_url=link_preview_url,
            preview_img_url=link_preview_img,
        )

    def __next__(self) -> TGPostDataclass:
        if len(self.q) > 0:
            head_post = self.q.pop(0)
            dataclass_item = self.html_tag_to_dataclass(head_post)

            if dataclass_item:
                return dataclass_item
            else:
                return self.__next__()
        elif not self.next_url:
            raise StopIteration
        else:  # No left fetched posts in queue
            print(f'Fetching new posts page')
            self.fetch_next_posts_page(self.next_url)

            return self.__next__()


if __name__ == "__main__":
    gen = iter(TGApiChannel('https://t.me/s/prostyemisli'))

    for i in range(101):
        c = next(gen)
        print(c)


class TGFeed(Feed):
    ContentItemClass = TGPostDataclass
    api_class = TGApiChannel
    username: str

    def __init__(self,
                 channel_username: str = None,
                 channel_url: str = None
                 ):
        if channel_url:
            channel_username = re.search('[^/]+(?=/$|$)', channel_url).group()

        self.username = channel_username
        super().__init__(f'https://t.me/s/{channel_username}')


def tg_gen_rss(
        feed: TGFeed,
        items: Sequence[TGPostDataclass],
        rss_format: RssFormat = RssFormat.Atom,
        use_enclosures: bool = False
):

    feed_url = feed.url

    indent_size = 25 + (RUN_IDENTIFIER % 10)
    indent_str = " " * (indent_size - (min(indent_size, len(feed.username))))

    feed_title = f'TG | {feed.username}{indent_str}| {feed.api_object.channel_name}'
    feed_desc = feed.api_object.channel_desc

    fg = FeedGenerator()

    fg.id(feed_url)
    fg.title(feed_title)
    fg.author({'name': feed_title, 'uri': feed_url})
    fg.link(href=feed_url, rel='alternate')
    fg.logo(feed.api_object.channel_img_url)
    if feed_desc:
        fg.subtitle(feed_desc)

    for i in reversed(items):
        link = i.url

        if TG_RSS_USE_HTML and i.html_content:
            content = i.html_content
            content_type = 'html'
        else:
            content = i.text
            content_type = None

        fe = fg.add_entry()
        fe.id(i.url)
        fe.title(shortened_text(i.text, 50))
        fe.content(content, type=content_type)
        fe.link(href=link)
        if use_enclosures and i.preview_img_url:
            fe.link(
                href=i.preview_img_url,
                rel='enclosure',
                type=f"{i.preview_img_url[i.preview_img_url.rfind('.') + 1:]}",
                length=str(len(logged_get(i.preview_img_url).content))
            )
        fe.published(i.pub_date)

    dirname = f'feeds'
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    dirname = os.path.join(dirname, feed.username)
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
