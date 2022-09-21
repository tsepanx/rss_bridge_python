import datetime
import pprint

import requests

API_KEY = open('.YT_API_KEY').readline()

def as_list(func):
    def wrapper(*args, **kwargs):
        res = list(func(*args, *kwargs))
        return res
    return wrapper


def _api_get_method(api_url: str, _params: dict) -> dict:
    print('Making request...')

    params = {"key": API_KEY}
    params.update(_params)

    req = requests.get(api_url, params=params)
    print(f'{req.status_code} | {req.url}')
    return req.json()


# @as_list
def last_channel_videos(
        channel_id: str = None,  # Channel id in str format
        days_after: int = None,  # Filter by v.date > (now - x days)
        count: int = None, **kwargs):  # Get last x videos ordered by date
    api_url = "https://www.googleapis.com/youtube/v3/search"

    MAX_LASTN = 1000

    _params = {
        "channelId": channel_id,
        "maxResults": count if count else MAX_LASTN,
        "order": "date",
        "part": "snippet",
        "type": "video",
    }

    if days_after:
        published_after_datetime = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_after)
        published_after_string = published_after_datetime.isoformat()
        print(published_after_string)
        _params.update({
            "published_after": published_after_string
        })

    _params.update(kwargs)
    res = _api_get_method(api_url, _params)
    return res['items']


if __name__ == "__main__":
    CHANNELS = [
        # "https://youtube.com/channel/UCPMus_VPfNJsNRwkrE3ySSA",
        # "https://youtube.com/channel/UC3Xbp3NcAtiq0XHOcU3QdOA",
        "https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg"
    ]

    ids = [i.split('/')[-1] for i in CHANNELS]
    id = ids[0]
    res = last_channel_videos(channel_id=id, days_after=7)
    # pprint.pprint(res)
