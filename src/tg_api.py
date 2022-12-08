import datetime
import re
from dataclasses import dataclass
from typing import Any, List, Optional, TypeVar, Union

import bs4
from fastapi import HTTPException

from .base import ApiChannel, Item
from .utils import (
    DEFAULT_TZ,
    TG_BASE_URL,
    TG_RSS_HTML_APPEND_PREVIEW,
    logged_get,
    shortened_text,
)


def derive_datetime_from_message_date_tag(parent_element) -> datetime.datetime | None:
    if not isinstance(parent_element, bs4.Tag):
        return None

    message_datetime_tag = parent_element.contents[0]

    if not isinstance(message_datetime_tag, bs4.Tag):
        return None

    datetime_str = message_datetime_tag.get("datetime")
    if not isinstance(datetime_str, str):
        return None

    post_date = datetime.datetime.fromisoformat(datetime_str).replace(
        tzinfo=DEFAULT_TZ
    )  # Convert from string to pythonic format
    return post_date


T = TypeVar("T")


def make_sure(res: Any, return_type: type[T]) -> T | None:
    if isinstance(res, return_type):
        return res
    return None


@dataclass
class TGPost(Item):
    preview_link_url: str | None = None

    @classmethod
    def from_raw_data(cls, data: bs4.Tag) -> Optional["TGPost"]:
        """
        :param data: bs4 Tag element that is wrapper of single TG channel message
        """
        post = data

        msg_date_parent_tag = post.findChild(
            name="a", attrs={"class": "tgme_widget_message_date"}
        )
        msg_date_parent_tag = make_sure(msg_date_parent_tag, bs4.Tag)

        message_datetime: datetime.datetime | None = (
            derive_datetime_from_message_date_tag(msg_date_parent_tag)
        )

        if msg_date_parent_tag:
            post_href = msg_date_parent_tag.get("href")
            post_href = make_sure(post_href, str)
        else:
            post_href = None

        text_wrapper = post.findChild(
            name="div", attrs={"class": "tgme_widget_message_text"}
        )

        if not text_wrapper:
            return None

        text = text_wrapper.get_text("\n", strip=True)
        html_content = str(text_wrapper)

        link_preview_wrapper = post.findChild(
            name="a", attrs={"class": "tgme_widget_message_link_preview"}
        )

        link_preview_wrapper = make_sure(link_preview_wrapper, bs4.Tag)

        if link_preview_wrapper:  # There is a preview section
            link_preview_url = link_preview_wrapper.get("href")
            link_preview_url = make_sure(link_preview_url, str)

            link_preview_img_tag = (
                post.findChild(name="i", attrs={"class": "link_preview_right_image"})
                or post.findChild(name="i", attrs={"class": "link_preview_image"})
                or post.findChild(name="i", attrs={"class": "link_preview_video_thumb"})
            )

            link_preview_img_tag = make_sure(link_preview_img_tag, bs4.Tag)

            if link_preview_img_tag:
                link_preview_img_tag_style = link_preview_img_tag.get("style")
                link_preview_img_tag_style = make_sure(link_preview_img_tag_style, str)
            else:
                link_preview_img_tag_style = None

            if link_preview_img_tag_style:
                r = r"background-image:url\('(.*)'\)"
                link_preview_img = re.findall(r, link_preview_img_tag_style)[0]
            else:
                link_preview_img = None

            link_preview_title = link_preview_wrapper.find(
                attrs={"class": "link_preview_title"}
            )
            link_preview_desc = link_preview_wrapper.find(
                attrs={"class": "link_preview_description"}
            )

            if TG_RSS_HTML_APPEND_PREVIEW:
                html_content += f"<br/>Preview content:<br/>{link_preview_title}<br/>{link_preview_desc}"
        else:
            link_preview_url = None
            link_preview_img = None

        title = shortened_text(text, 50)

        return cls(
            url=post_href,
            pub_date=message_datetime,
            title=title,
            text_content=text,
            html_content=html_content,
            preview_link_url=link_preview_url,
            preview_img_url=link_preview_img,
        )

    def __repr__(self):
        return f"{self.url} | {self.title} | {self.pub_date} | {self.preview_link_url}"


class TGApiChannel(ApiChannel):
    """
    Basic api related class representing single telegram channel
    fetch_items(<filters_kwargs>) returns channel messages ("ItemClass") ordered by pub date
    """

    ItemClass: type[Item] = TGPost

    SUPPORT_FILTER_BY_DATE = False
    q: List[bs4.element.Tag] = list()
    next_url: str | None = None

    def __init__(self, url_or_alias: str):
        name_match = re.search("[^/]+(?=/$|$)", url_or_alias)
        if not name_match:
            raise Exception

        channel_username = name_match.group()

        self.username = channel_username or url_or_alias
        url = f"https://t.me/s/{channel_username}"

        self.next_url = url  # TODO make it common in ApiChannel
        super().__init__(url=url)

    def fetch_metadata(self):
        super().fetch_metadata()

        req = logged_get(self.url)
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        # --- Parse channel title ---
        channel_metadata_wrapper = soup.find(
            name="div", attrs={"class": "tgme_channel_info_header"}, recursive=True
        )

        if channel_metadata_wrapper is None:
            raise HTTPException(
                status_code=404,
                detail=f"Telegram: channel with username @{self.username} not found",
            )
        channel_title = channel_metadata_wrapper.findChild(name="span").contents[0]

        channel_img_url = channel_metadata_wrapper.findChild(name="img", recursive=True)
        channel_img_url = channel_img_url.get("src")

        try:
            channel_desc = soup.findChild(
                name="div",
                attrs={"class": "tgme_channel_info_description"},
                recursive=True,
            ).contents[0]
        except AttributeError:
            channel_desc = ""

        self.full_name = str(channel_title)
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
        print("TG: NEW CHUNK | ", end="")
        req = logged_get(fetch_url)
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        # --- Get list of posts wrappers
        posts_list = soup.findChildren(
            name="div", attrs={"class": "tgme_widget_message_wrap"}, recursive=True
        )

        self.q.extend(reversed(posts_list))  # TODO convert to dataclass on the fly

        # --- Next messages page href parsing
        messages_more_tag = soup.find(
            name="a", attrs={"class": "tme_messages_more"}, recursive=True
        )

        if not messages_more_tag:
            print("Retrying fetch_items...")
            self.on_fetch_new_chunk(fetch_url)  # Try to fetch_items again

        if isinstance(messages_more_tag, bs4.Tag):
            if messages_more_tag.get("data-after"):  # We reached end of posts list
                self.next_url = None
            else:
                next_page_href = messages_more_tag.get("href")
                next_page_link = f"{TG_BASE_URL}{next_page_href}"

                self.next_url = next_page_link

    def fetch_next(self):
        return self.on_fetch_new_chunk(self.next_url)

    def is_iteration_ended(self):
        return not self.next_url
