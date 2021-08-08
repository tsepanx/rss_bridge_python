import re
import requests
import logging

import utils

API_KEY = open('.YT_API_KEY').readline()

REQUESTS_MADE = 0

class YoutubeApi:

    @classmethod
    def __get(self, api_url, _params):
        global REQUESTS_MADE

        print('Making request...')
        REQUESTS_MADE += 1

        params = {"key": API_KEY}

        params.update(_params)

        d = requests.get(api_url, params=params).json()

        return d

    @classmethod
    def channel_videos(self, channel_id=None, **kwargs):
        api_url = "https://www.googleapis.com/youtube/v3/search"

        _params = {
            "channelId": channel_id,
            "maxResults": "1000",
            "order": "date",
            "part": "snippet",
            "type": "video",
        }

        _params.update(kwargs)

        return YoutubeApi.__get(api_url, _params)

class Video:
    def __init__(self, _id, title=None):
        self.id = _id
        self.title = title

    @property
    def url(self):
        return 'https://youtu.be/' + self.id #TODO replace with normal link

    @property
    def preview_url(self):
        return f'https://i.ytimg.com/vi/{self.id}/hqdefault.jpg'

    def __str__(self):
        return f'id {self.id} | title {self.title}'

    def __repr__(self):
        return f'\nid {self.id} | title {self.title}'

class Channel:
    def __init__(self, url=None, username=None, videos=[]):
        self.url = url
        self.username = username
        self.videos = videos

    @property
    def id(self):
        r = '(?<=channel\/)([A-z]|[0-9])+'
        return re.search(r, self.url).group()

    def fetch_videos(self):
        def fetch(ptoken=None):
            params = dict()
            if ptoken:
                params[utils.ApiField.PAGE_TOKEN] = ptoken

            d = YoutubeApi.channel_videos(self.id, **params)

            try:
                new_videos = list(utils.channel_videos_from_search(d, Video))
                self.videos.extend(new_videos)

                return d
            except Exception as e:
                print(d)
                exit()

        d = fetch(None)

        while utils.ApiField.NEXT_PAGE_TOKEN in d:
            d = fetch(ptoken=d[utils.ApiField.NEXT_PAGE_TOKEN])



    def __str__(self):
        return f"Channel {self.id}, {len(self.videos)} videos"


CHANNELS = [
    # "https://youtube.com/channel/UCPMus_VPfNJsNRwkrE3ySSA",
    # "https://youtube.com/channel/UC3Xbp3NcAtiq0XHOcU3QdOA",
    "https://youtube.com/channel/UCVls1GmFKf6WlTraIb_IaJg"
]

if __name__ == '__main__':
    for url in CHANNELS:
        ch = Channel(url=url)

        print()
        print(ch)

        ch.fetch_videos()
        print(ch.videos)

    print(REQUESTS_MADE, 'requests made')
