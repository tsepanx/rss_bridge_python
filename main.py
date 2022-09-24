from tg_api import TGFeed
from utils import gen_rss, last_n_weeks

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":

    # TODO return to datetime
    # TODO html as content in rss

    # tg_alias = 'black_triangle_tg'
    # feed = TGFeed(tg_alias)
    # feed.fetch_all(
    #     last_n_weeks(1)
    # )

    aliases = list(
        filter(
            lambda x: not x.startswith('#'),
            map(
                str.strip,
                open('tg_aliases').readlines()
            )
        )
    )

    for i in aliases:
        f = TGFeed(i)
        items = f.fetch_all(after_date=last_n_weeks(1))

        gen_rss(items,
                feed_url=f.url,
                feed_title=f.tg_alias,
                feed_desc=f.api_object.channel_desc)
