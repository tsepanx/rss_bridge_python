import datetime
import re
from dataclasses import dataclass
from typing import List, Optional

import bs4

from .base import ApiChannel, ItemDataclass, ItemDataclassType
from .utils import (
    DEFAULT_TZ,
    TG_BASE_URL,
    TG_RSS_HTML_APPEND_PREVIEW,
    TG_RSS_USE_HTML,
    logged_get,
    shortened_text,
)


@dataclass
class TGPostDataclass(ItemDataclass):
    preview_link_url: Optional[str] = None

    @classmethod
    def from_raw_data(cls, data: bs4.element.Tag) -> Optional["TGPostDataclass"]:
        """
        :param data: bs4 Tag element that is wrapper of single TG channel message
        """
        post = data

        href_date_tag = post.findChild(
            name="a", attrs={"class": "tgme_widget_message_date"}
        )
        datetime_str = href_date_tag.contents[0].get("datetime")
        post_date = datetime.datetime.fromisoformat(datetime_str).replace(
            tzinfo=DEFAULT_TZ
        )  # Convert from string to pythonic format

        post_href = href_date_tag.get("href")

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

        if link_preview_wrapper:  # There is a preview section
            link_preview_url = link_preview_wrapper.get("href")

            link_preview_img_tag = (
                post.findChild(name="i", attrs={"class": "link_preview_right_image"})
                or post.findChild(name="i", attrs={"class": "link_preview_image"})
                or post.findChild(name="i", attrs={"class": "link_preview_video_thumb"})
            )

            if link_preview_img_tag:
                link_preview_img_tag_style = link_preview_img_tag.get("style")
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
            link_preview_title = None
            link_preview_desc = None

        title = shortened_text(text, 50)

        return cls(
            pub_date=post_date,
            url=post_href,
            title=title,
            text_content=text,
            html_content=html_content if TG_RSS_USE_HTML else None,
            preview_link_url=link_preview_url,
            preview_img_url=link_preview_img,
        )

    def __repr__(self):
        return f"{self.url} | {self.title} | {self.pub_date} | {self.preview_link_url}"


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
        channel_username = re.search("[^/]+(?=/$|$)", url_or_alias).group()

        self.username = channel_username or url_or_alias
        url = f"https://t.me/s/{channel_username}"

        self.next_url = url  # TODO make it common in ApiChannel
        super().__init__(url=url)

    def fetch_metadata(self):
        print("\nMETADATA | ", end="")
        req = logged_get(self.url)
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        # --- Parse channel title ---
        channel_metadata_wrapper = soup.find(
            name="div", attrs={"class": "tgme_channel_info_header"}, recursive=True
        )

        channel_title = channel_metadata_wrapper.findChild(name="span").contents[0]

        channel_img_url = channel_metadata_wrapper.findChild(name="img", recursive=True)
        channel_img_url = channel_img_url.get("src")

        channel_desc = soup.findChild(
            name="div", attrs={"class": "tgme_channel_info_description"}, recursive=True
        ).contents[0]

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
        print(f"TG: NEW CHUNK | ", end="")
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

        if messages_more_tag.get("data-after"):  # We reached end of posts list
            self.next_url = None
        else:
            next_page_href = messages_more_tag.get("href")
            next_page_link = f"{TG_BASE_URL}{next_page_href}"

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
