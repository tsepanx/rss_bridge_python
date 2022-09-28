from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Type, Sequence, TypeVar, Any, Generator

from .utils import to_tg_datetime, DEFAULT_MAX_ENTRIES_TO_FETCH


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
    def from_raw_data(cls, _: Any) -> Optional['ItemDataclassType']:
        pass


ItemDataclassType = TypeVar('ItemDataclassType', bound=ItemDataclass)

class ApiChannel:
    ItemDataclassClass: ItemDataclassType  # = ItemDataclass
    SUPPORT_FILTER_BY_DATE: Optional[
        bool] = False  # If api allow fetching items with date > self._published_after_param
    _published_after_param: Optional[date] = None
    q: List = list()
    url: str

    username: str = None
    logo_url: Optional[str] = None
    description: Optional[str] = None

    def __init__(self, url: str):
        self.url = url
        self.q = list()
        self.fetch_metadata()

    def next(self) -> 'ItemDataclassClass': pass

    def fetch_metadata(self):
        pass

    def fetch_items(self, all=False, entries_count: int = None, after_date: date = None) -> Sequence[ItemDataclassType]:
        """
        Base function to get new updates from given feed.
        Must be overridden by every Sub-class.
        :return: list of fetched entries
        """

        # if not (after_date or entries_count):
        #     entries_count = DEFAULT_MAX_ENTRIES_TO_FETCH
        if not (all or entries_count or after_date):
            entries_count = DEFAULT_MAX_ENTRIES_TO_FETCH

        if after_date:
            if self.SUPPORT_FILTER_BY_DATE:
                self._published_after_param = after_date
                return self.fetch_items(
                    all=all,
                    entries_count=entries_count,
                    after_date=None
                )

        def inner() -> Generator:
            try:
                i = 0
                while c := self.next():
                    c: ItemDataclassType
                    if entries_count:  # Limited by max count of entries
                        if i >= entries_count:
                            return
                    if after_date:  # Limited by min date
                        if c.pub_date > to_tg_datetime(after_date):
                            return
                    yield c
                    i += 1
            except StopIteration:
                return

        return list(inner())


class ApiItem:
    """
    Responsible for fetching single item from API
    """
    ItemDataclassClass: ItemDataclassType
    item_object: 'ItemDataclassClass'

    def __init__(self, url: str):
        self.url = url

    def fetch_data(self) -> 'ItemDataclassClass':
        pass


# class Feed:
#     ApiChannelClass: Type[ApiChannel]  # = ApiChannel
#     _api_object: ApiChannel = None
#
#     def __init__(self, url: str):
#         self.url = url
#         self._api_object = self.ApiChannelClass(url)

    # def fetch_items(self, all=False, entries_count: int = None, after_date: date = None) -> Sequence[ItemDataclassType]:
    #     """
    #     Base function to get new updates from given feed.
    #     Must be overridden by every Sub-class.
    #     :return: list of fetched entries
    #     """
    #
    #     # if not (after_date or entries_count):
    #     #     entries_count = DEFAULT_MAX_ENTRIES_TO_FETCH
    #     if not (all or entries_count or after_date):
    #         entries_count = DEFAULT_MAX_ENTRIES_TO_FETCH
    #
    #     if after_date:
    #         if self.ApiChannelClass.SUPPORT_FILTER_BY_DATE:
    #             self._api_object._published_after_param = after_date
    #             return self.fetch_items(
    #                 all=all,
    #                 entries_count=entries_count,
    #                 after_date=None
    #             )
    #
    #     def inner() -> Generator:
    #         try:
    #             i = 0
    #             while c := next(self._api_object):
    #                 c: ItemDataclassType
    #                 if entries_count:  # Limited by max count of entries
    #                     if i >= entries_count:
    #                         return
    #                 if after_date:  # Limited by min date
    #                     if c.pub_date > to_tg_datetime(after_date):
    #                         return
    #                 yield c
    #                 i += 1
    #         except StopIteration:
    #             return
    #
    #     return list(inner())

    # def __iter__(self):
    #     raise Exception('Iteration not allowed. use Feed.fetch_items()')
    #
    # @property
    # def channel_name(self):
    #     return self._api_object.channel_name
    #
    # @property
    # def description(self):
    #     return self._api_object.description
    #
    # @property
    # def logo_url(self):
    #     return self._api_object.logo_url
