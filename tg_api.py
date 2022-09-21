import datetime
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import bs4
import requests

BASE_URL = 'https://t.me'


@dataclass
class TGApiPost:
    datetime: datetime.datetime
    url: str
    text: str = None
    preview_link: str = None
    preview_link_pic: str = None

def logged_get(url):
    res = requests.get(url)
    print(f'REQUEST: {url}')
    return res

class TGChannelPosts:
    q = list()
    next_url: str = None

    def __init__(self, url: str):
        self.url = url

        self.next_url = self.fetch_next_posts_page(self.url)

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

    @lru_cache
    def fetch_next_posts_page(self, fetch_url: str) -> Optional[str]:
        """
        :param fetch_url: Link to fetch previous channel posts.
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

        self.q = list(reversed(posts_list))

        # --- Next messages page href parsing
        messages_more_tag = soup.find(
            name='a', attrs={'class': 'tme_messages_more'},
            recursive=True
        )

        if messages_more_tag.get('data-after'):
            # raise StopIteration
            return None  # We reached end of posts list

        next_page_href = messages_more_tag.get('href')
        next_page_link = f'{BASE_URL}{next_page_href}'
        return next_page_link

    @staticmethod
    def html_tag_to_dataclass(post: bs4.element.Tag) -> Optional[TGApiPost]:
        href_date_tag = post.findChild(name='a', attrs={'class': 'tgme_widget_message_date'})
        post_date = href_date_tag.contents[0].get('datetime')
        post_date = datetime.datetime.fromisoformat(post_date)  # Convert from string to pythonic format

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

        return TGApiPost(
            datetime=post_date,
            url=post_href,
            text=text,
            preview_link=link_preview,
            preview_link_pic=link_preview_img,
        )

    def __iter__(self):
        return self

    def __next__(self) -> TGApiPost:
        if len(self.q) > 0:
            next_post = self.q[0]
            self.q.pop(0)

            post_dataclass = self.html_tag_to_dataclass(next_post)
            if post_dataclass:
                return post_dataclass
            else:
                return self.__next__()

        else:  # No left fetched posts
            print(f'Fetching new posts page')
            if self.next_url:
                self.next_url = self.fetch_next_posts_page(self.next_url)
                return self.__next__()
            else:
                raise StopIteration


if __name__ == "__main__":
    gen = TGChannelPosts('https://t.me/s/prostyemisli')

    # for i in range(200):
    #     c = gen.__next__()
    #     print(f'href: "{c.url}"')
    #     print(f'text: "{c.text}"')
    #     print(f'datetime: "{c.datetime}"')
    #     print('\n\n')

    for i in list(gen):
        print(i.url)
