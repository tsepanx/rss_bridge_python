import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

from tg_api import TGFeed, tg_gen_rss
from utils import RssFormat, last_n_weeks

app = FastAPI()


@app.get('/tg-feed/{username}', response_class=FileResponse)
async def root(username: str, rss_format: RssFormat = RssFormat.Atom):
    tg_feed = TGFeed(channel_username=username)

    items = tg_feed.fetch_all(
        # last_n_entries=5
        after_date=last_n_weeks(1)
    )

    path = tg_gen_rss(
        feed=tg_feed,
        items=items,
        rss_format=rss_format
    )

    return FileResponse(
        path=path,
        media_type='text/xml'
    )

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8080
    )


# if __name__ == "__main__":
#     # TODO html as content in rss

    # TGFeed(channel_url='https://t.me/s/black_triangle_tg')

    # channel_username = 'black_triangle_tg'
    # feed = TGFeed(channel_username)
    # feed.fetch_all(
    #     last_n_weeks(1)
    # )

    # aliases = list(
    #     filter(
    #         lambda x: not x.startswith('#'),
    #         map(
    #             str.strip,
    #             open('tg_aliases').readlines()
    #         )
    #     )
    # )
    #
    # for i in aliases:
    #     f = TGFeed(i)
    #     items = f.fetch_all(after_date=last_n_weeks(1))
    #
    #     tg_gen_rss(items,
    #             feed_url=f.url,
    #             feed_title=f.channel_username,
    #             feed_desc=f.api_object.channel_desc)
