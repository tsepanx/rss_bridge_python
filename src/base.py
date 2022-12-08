import datetime
from dataclasses import dataclass
from typing import Any, Generator, Generic, List, Optional, ParamSpec, Sequence, TypeVar

from .utils import date_to_datetime


@dataclass
class Item:
    """
    Base interface defining Feed.fetch_items() return type
    """

    # id: int  # Unique attr
    url: str | None
    pub_date: datetime.datetime | None
    title: str | None = None
    text_content: str | None = None
    html_content: str | None = None
    preview_img_url: str | None = None

    @classmethod
    def from_raw_data(cls, _: Any) -> Optional["Item"]:
        pass


# TODO
# ItemDataclassType = TypeVar("ItemDataclassType", bound=Item)
# T = TypeVar("T", bound=Item)


class ApiChannel:
    ItemClass = Item
    url: str

    # Fetching related attrs
    SUPPORT_FILTER_BY_DATE = False  # If api supports fetching items filtered by date > self._published_after_param
    _published_after_param: Optional[datetime.date]
    q: List = list()
    max_requests = float("inf")

    # Metadata
    username: str | None = None
    full_name: str | None = None
    logo_url: str | None = None
    description: str | None = None

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
        entries_count: int | None = None,
        max_requests: int | None = None,
        after_date: datetime.date | None = None,
    ) -> Sequence[ItemClass]:
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
                c: Item
                while c := self.__next():
                    if (
                        entries_count and i >= entries_count
                    ):  # Limited by max count of entries
                        return
                    if (
                        after_date
                        and c.pub_date
                        and c.pub_date > date_to_datetime(after_date)
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

    def __next(self):  # -> T:  # TODO Maybe change this method
        if len(self.q) > 0:
            head_post = self.q.pop(0)
            dataclass_item = self.ItemClass.from_raw_data(head_post)

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

    ItemClass: type[Item] = Item
    item_object: "ItemClass"

    def __init__(self, url: str):
        self.url = url

    def fetch_data(self) -> "ItemClass":
        pass
