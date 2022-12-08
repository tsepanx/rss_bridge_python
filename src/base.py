import datetime
from dataclasses import dataclass
from typing import Any, Generator, List, Optional, Sequence

from .utils import date_to_datetime


@dataclass
class ItemDataclass:
    """
    Base interface defining Feed.fetch_items() return type
    """

    # id: int  # Unique attr
    url: str
    pub_date: datetime.datetime
    title: Optional[str]
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    preview_img_url: Optional[str] = None

    @classmethod
    def from_raw_data(cls, _: Any) -> type["ItemDataclass"] | None:
        pass


# ItemDataclassType = TypeVar("ItemDataclassType", bound=ItemDataclass)


class ApiChannel:
    ItemDataclassClass: type[ItemDataclass]  # ItemDataclassType  # = ItemDataclass
    url: str

    # Fetching related attrs
    SUPPORT_FILTER_BY_DATE = False  # If api supports fetching items filtered by date > self._published_after_param
    _published_after_param: Optional[datetime.date]
    q: List = list()
    max_requests = float("inf")

    # Metadata
    username: str = None
    full_name: str = None
    logo_url: Optional[str] = None
    description: Optional[str] = None

    def __init__(self, url: str):
        self.url = url
        self.reset_fetch_fields()
        if not self.is_fetched_metadata():
            self.fetch_metadata()

    def reset_fetch_fields(self):
        self.q = list()
        self.max_requests = float("inf")
        self._published_after_param = None

    def is_fetched_metadata(self):
        pass

    def fetch_metadata(self):
        print("\nMETADATA | ", end="")

    def fetch_next(self):
        pass

    # @my_lru_cache
    def fetch_items(
        self,
        fetch_all=False,
        entries_count: int = None,
        max_requests: int = None,
        after_date: datetime.date = None,
    ) -> Sequence["ItemDataclassClass"]:
        """
        Base function to get new updates from given feed.

        When no params passed, set max_requests = 1,
        to limit made requests count

        :returns: list of fetched entries
        """

        if not (
            fetch_all
            or entries_count
            or max_requests
            or after_date
            or self._published_after_param
        ):
            self.max_requests = 1
        elif max_requests:
            self.max_requests = max_requests

        if after_date and self.SUPPORT_FILTER_BY_DATE:
            self._published_after_param = after_date
            return self.fetch_items(
                fetch_all=fetch_all, entries_count=entries_count, after_date=None
            )

        def inner() -> Generator:
            try:
                i = 0
                while c := self.__next():
                    c: ItemDataclass
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

    def is_iteration_ended(self):
        pass

    def __next(self) -> "ItemDataclassClass":  # TODO Maybe change this method
        if len(self.q) > 0:
            head_post = self.q.pop(0)
            dataclass_item = self.ItemDataclassClass.from_raw_data(head_post)

            return dataclass_item if dataclass_item else self.__next()
        elif self.is_iteration_ended():
            self.reset_fetch_fields()
            raise StopIteration
        else:  # No left fetched posts in queue
            if self.max_requests > 0:
                self.fetch_next()
                self.max_requests -= 1
                return self.__next()
            else:
                raise StopIteration


class ApiItem:
    """
    Responsible for fetching single item from API
    """

    ItemDataclassClass: type[ItemDataclass]
    item_object: "ItemDataclassClass"

    def __init__(self, url: str):
        self.url = url

    def fetch_data(self) -> "ItemDataclassClass":
        pass
