import datetime
import re
from dataclasses import (
    dataclass,
)
from typing import (
    List,
    Optional,
)

import bs4
import fastapi
from fastapi import (
    HTTPException,
)

from .base import (
    ApiChannel,
    Item,
)
from .parsing import (
    PreviewAttrs,
    derive_post_datetime,
    derive_post_text,
    derive_post_url,
    derive_preview_attrs,
)
from .utils import (
    TG_BASE_URL,
    TG_RSS_HTML_APPEND_PREVIEW,
    form_preview_html_text,
    logged_get,
    shortened_text,
)


@dataclass
class TGPost(Item):
    preview_link_url: str | None = None

    @classmethod
    def from_raw_data(cls, data: bs4.Tag) -> Optional["TGPost"]:
        """
        :param data: bs4 Tag element that is wrapper of single TG channel message
        """

        message_datetime: datetime.datetime | None = derive_post_datetime(data)
        post_url: str | None = derive_post_url(data)

        text_attrs = derive_post_text(data)
        if text_attrs is None:  # No text in post
            return None

        text, html_content = text_attrs
        link_preview_attrs: PreviewAttrs = derive_preview_attrs(data)

        if TG_RSS_HTML_APPEND_PREVIEW:
            if link_preview_attrs.title and link_preview_attrs.desc:
                html_content += form_preview_html_text(link_preview_attrs.title, link_preview_attrs.desc)

        title = shortened_text(text, 50)

        return cls(
            url=post_url,
            pub_date=message_datetime,
            title=title,
            text_content=text,
            html_content=html_content,
            preview_link_url=link_preview_attrs.url,
            preview_media_url=link_preview_attrs.media_url,
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
    q: List[bs4.element.Tag] = []
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
        channel_metadata_wrapper = soup.find(name="div", attrs={"class": "tgme_channel_info_header"}, recursive=True)

        if channel_metadata_wrapper is None:
            raise HTTPException(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
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
    def on_fetch_new_chunk(self, fetch_url: str, retry_more=True):  # -> Optional[str]:
        """
        :param fetch_url: Link to previous channel posts.
        :param retry_more Flag indicates whether this func can be called recursively again or not
        example: https://t.me/s/notboring_tech?before=2422

        :return: Next fetch_url for fetching next page of posts
        """
        print("TG: NEW CHUNK | ", end="")
        req = logged_get(fetch_url)
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        # --- Get list of posts wrappers
        posts_list = soup.findChildren(name="div", attrs={"class": "tgme_widget_message_wrap"}, recursive=True)

        self.q.extend(reversed(posts_list))  # TODO convert to dataclass on the fly

        # --- Next messages page href parsing
        messages_more_tag = soup.find(name="a", attrs={"class": "tme_messages_more"}, recursive=True)

        if not messages_more_tag:
            if retry_more:
                print("Retrying fetch_items...")
                self.on_fetch_new_chunk(fetch_url, retry_more=False)  # Try to fetch_items again

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
