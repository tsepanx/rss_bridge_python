import datetime
import functools
import re
from typing import (
    NamedTuple,
)

import bs4

from src.utils import (
    DEFAULT_TZ,
    make_sure,
)


def derive_post_datetime(post_element: bs4.Tag) -> datetime.datetime | None:
    post_date_parent_tag = post_element.findChild(name="a", attrs={"class": "tgme_widget_message_date"})
    post_date_parent_tag = make_sure(post_date_parent_tag, bs4.Tag)

    if not post_date_parent_tag:
        return None

    post_datetime_tag = make_sure(post_date_parent_tag.contents[0], bs4.Tag)

    if not post_datetime_tag:
        return None

    datetime_str = post_datetime_tag.get("datetime")
    datetime_str = make_sure(datetime_str, str)

    if not datetime_str:
        return None

    post_date = datetime.datetime.fromisoformat(datetime_str).replace(
        tzinfo=DEFAULT_TZ
    )  # Convert from string to pythonic format
    return post_date


def derive_post_url(post_element: bs4.Tag):
    post_date_parent_tag = post_element.findChild(name="a", attrs={"class": "tgme_widget_message_date"})
    post_date_parent_tag = make_sure(post_date_parent_tag, bs4.Tag)

    if post_date_parent_tag:
        post_href = post_date_parent_tag.get("href")
        post_href = make_sure(post_href, str)
    else:
        post_href = None

    return post_href


def derive_post_text(post_element: bs4.Tag) -> tuple[str, str] | None:
    text_wrapper = post_element.findChild(name="div", attrs={"class": "tgme_widget_message_text"})
    text_wrapper = make_sure(text_wrapper, bs4.PageElement)  # type: ignore

    if not text_wrapper:
        return None

    html_text = str(text_wrapper)
    text = text_wrapper.get_text("\n", strip=True)
    return text, html_text


class PreviewAttrs(NamedTuple):
    url: str | None = None
    media_url: str | None = None
    desc: str | None = None
    title: str | None = None


def derive_preview_attrs(post_element: bs4.Tag) -> PreviewAttrs:
    link_preview_wrapper = post_element.findChild(name="a", attrs={"class": "tgme_widget_message_link_preview"})
    link_preview_wrapper = make_sure(link_preview_wrapper, bs4.Tag)

    if not link_preview_wrapper:
        return PreviewAttrs()

    link_preview_url = link_preview_wrapper.get("href")
    link_preview_url = make_sure(link_preview_url, str)

    # --- Trying to match different types of message preview
    possible_image_tag_class = [
        "link_preview_right_image",
        "link_preview_image",
        "link_preview_video_thumb",
    ]
    link_preview_img_tag_list = [post_element.findChild(name="i", attrs={"class": i}) for i in possible_image_tag_class]
    # ---

    link_preview_img_tag = functools.reduce(lambda a, b: a or b, link_preview_img_tag_list)
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

    link_preview_title = str(link_preview_wrapper.find(attrs={"class": "link_preview_title"}))
    link_preview_desc: str = str(link_preview_wrapper.find(attrs={"class": "link_preview_description"}))

    return PreviewAttrs(
        url=link_preview_url,
        media_url=link_preview_img,
        desc=link_preview_desc,
        title=link_preview_title,
    )
