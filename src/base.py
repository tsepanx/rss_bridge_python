from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Generator, List, Optional, Sequence, TypeVar

from .utils import DEFAULT_MAX_ENTRIES_TO_FETCH, date_to_datetime


@dataclass
class ItemDataclass:
    """
    Base interface defining Feed.fetch_items() return type
    """

    # id: int  # Unique attr
    url: str
    pub_date: datetime
    title: Optional[str]
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    preview_img_url: Optional[str] = None

    @classmethod
    def from_raw_data(cls, _: Any) -> Optional["ItemDataclassType"]:
        pass


ItemDataclassType = TypeVar("ItemDataclassType", bound=ItemDataclass)


class ApiChannel:
    ItemDataclassClass: ItemDataclassType  # = ItemDataclass
    SUPPORT_FILTER_BY_DATE: Optional[
        bool
    ] = False  # If api allow fetching items with date > self._published_after_param
    _published_after_param: Optional[date] = None
    q: List = list()
    url: str

    username: str = None
    full_name: str = None
    logo_url: Optional[str] = None
    description: Optional[str] = None

    def __init__(self, url: str):
        self.url = url
        self.q = list()
        self.fetch_metadata()

    def reset_fetch_fields(self):
        self.q = list()

    def next(self) -> "ItemDataclassClass":
        pass

    def fetch_metadata(self):
        pass

    def fetch_items(
        self, all=False, entries_count: int = None, after_date: date = None
    ) -> Sequence[ItemDataclassType]:
        """
        Base function to get new updates from given feed.

        When no params passed, set entries_count = DEFAULT_MAX_ENTRIES_TO_FETCH,
        to limit made requests count

        :returns: list of fetched entries
        """

        if not (all or entries_count or after_date):
            entries_count = DEFAULT_MAX_ENTRIES_TO_FETCH
        elif after_date:
            if self.SUPPORT_FILTER_BY_DATE:
                self._published_after_param = after_date
                return self.fetch_items(
                    all=all, entries_count=entries_count, after_date=None
                )

        def inner() -> Generator:
            try:
                i = 0
                while c := self.next():
                    c: ItemDataclassType
                    if (
                        entries_count and i >= entries_count
                    ):  # Limited by max count of entries
                        return
                    if after_date and c.pub_date > date_to_datetime(
                        after_date
                    ):  # Limited by min date
                        return
                    yield c
                    i += 1
            except StopIteration:
                return

        res = list(inner())
        self.reset_fetch_fields()
        return res


class ApiItem:
    """
    Responsible for fetching single item from API
    """

    ItemDataclassClass: ItemDataclassType
    item_object: "ItemDataclassClass"

    def __init__(self, url: str):
        self.url = url

    def fetch_data(self) -> "ItemDataclassClass":
        pass
