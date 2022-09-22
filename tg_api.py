import datetime
import re
from dataclasses import dataclass
from typing import Optional, List

import bs4

from utils import shortened_text, logged_get, ContentItem, ApiClass, TG_BASE_URL


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
        self.next_url = url

        super().__init__(
            url=url
        )

    def fetch_channel_name(self):
        req = logged_get(self.url)
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        # --- Parse channel title ---
        channel_title_wrapper = soup.find(
            name='div', attrs={
                'class': 'tgme_channel_info_header_title'},
            recursive=True
        )
        channel_title_tag = channel_title_wrapper.findChild(name='span')
        channel_name = channel_title_tag.contents[0]
        print(channel_name)

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

        self.q.extend(
            list(reversed(posts_list))
        )  # TODO convert to dataclass on the fly

        # --- Next messages page href parsing
        messages_more_tag = soup.find(
            name='a', attrs={'class': 'tme_messages_more'},
            recursive=True
        )

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
        post_date = datetime.datetime.fromisoformat(datetime_str).date()  # Convert from string to pythonic format

        post_href = href_date_tag.get('href')

        text_wrapper = post.findChild(name='div', attrs={'class': 'tgme_widget_message_text'})
        if not text_wrapper:
            return None
        text = text_wrapper.get_text('\n', strip=True)

        link_preview_wrapper = post.findChild(name='a', attrs={'class': 'tgme_widget_message_link_preview'})

        if link_preview_wrapper:  # There is a preview section
            link_preview = link_preview_wrapper.get('href')

            link_preview_img_tag = post.findChild(name='i', attrs={'class': 'link_preview_right_image'})
            if link_preview_img_tag is None:
                link_preview_img_tag = post.findChild(name='i', attrs={'class': 'link_preview_image'})

            link_preview_img_tag_style = link_preview_img_tag.get('style')
            r = r"background-image:url\('(.*)'\)"
            link_preview_img = re.findall(r, link_preview_img_tag_style)[0]
        else:
            link_preview = None
            link_preview_img = None

        return TGPostDataclass(
            pub_date=post_date,
            url=post_href,
            text=text,
            preview_link_url=link_preview,
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
