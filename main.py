import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

from tg_api import TGFeed, tg_gen_rss
from utils import RssFormat, last_n_weeks

app = FastAPI()


@app.get('/tg-feed/{username}', response_class=FileResponse)
async def get_tg_feed(
        username: str,
        rss_format: RssFormat = RssFormat.Atom,
        max_items: Optional[int] = None,
        days: Optional[int] = None
):
    tg_feed = TGFeed(channel_username=username)

    if days:
        after_date = datetime.date.today() - datetime.timedelta(1) * days
    else:
        after_date = None

    if not (max_items or after_date):
        max_items = 20

    items = tg_feed.fetch_all(
        entries_count=max_items,
        after_date=after_date
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
