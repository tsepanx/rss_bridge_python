import datetime
import re
from dataclasses import dataclass
from typing import Iterable

import bs4
import requests


@dataclass
class TGApiPost:
    datetime: datetime.datetime
    url: str
    text: str = None
    preview_link: str = None
    preview_link_pic: str = None


def parse_channel_posts(url: str) -> Iterable[TGApiPost]:
    req = requests.get(url)
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    a = soup.find(
        name='div',
        attrs={
            'class': 'tgme_channel_info_header_title'},
        recursive=True)
    b = a.findChild(
        name='span'
    )

    channel_name = b.contents[0]
    print(channel_name)

    # ---

    posts_wrapper = soup.find(
        name='section',
        attrs={
            'class': 'tgme_channel_history'
        },
        recursive=True
    )

    posts_list = posts_wrapper.findChildren(
        name='div',
        attrs={
            'class': 'tgme_widget_message_wrap'
        },
        recursive=True
    )

    for post in list(reversed(posts_list))[:3]:
        href_date_elem = post.findChild(
            name='a',
            attrs={
                'class': 'tgme_widget_message_date'
            }
        )
        post_date = href_date_elem.contents[0].get_attribute_list('datetime')[0]
        post_date = datetime.datetime.fromisoformat(post_date)  # Convert to pythonic format
        print(post_date)

        post_href = href_date_elem.get_attribute_list('href')[0]
        print(post_href)

        text_wrapper = post.findChild(name='div', attrs={'class': 'tgme_widget_message_text'})
        text = text_wrapper.get_text('\n', strip=True)
        print(f'text: "{text}"')

        link_preview_wrapper = post.findChild(name='a', attrs={'class': 'tgme_widget_message_link_preview'})
        link_preview = link_preview_wrapper.get_attribute_list('href')

        link_preview_img_elem = post.findChild(name='i', attrs={'class': 'link_preview_right_image'})
        link_preview_img_elem_style = link_preview_img_elem.get_attribute_list('style')[0]
        r = r"background-image:url\('(.*)'\)"
        link_preview_img = re.findall(r, link_preview_img_elem_style)[0]

        print()

        dc = TGApiPost(
            datetime=post_date,
            url=post_href,
            text=text,
            preview_link=link_preview,
            preview_link_pic=link_preview_img,
        )

        # yield dc
        # exit()


if __name__ == "__main__":
    parse_channel_posts('https://t.me/s/prostyemisli')
