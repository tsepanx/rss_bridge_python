import enum


class VideoField:
    ID = "yt_videoid"
    URL = "link"
    TITLE = "title"


class ApiField:
    PAGE_TOKEN = "pageToken"
    NEXT_PAGE_TOKEN = "nextPageToken"

def channel_videos_from_search(d: dict, instance_type):
    items = d['items']

    for i in range(len(items)):
        videoId = 'videoId'
        
        if videoId in items[i]['id']:

            video_id = items[i]['id'][videoId]
            title = items[i]['snippet']['title']

            yield instance_type(video_id, title)
