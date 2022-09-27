import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse


from src.tg_api import TGFeed, tg_gen_rss
from src.utils import RssFormat

app = FastAPI()


@app.get('/tg-feed/{username}', response_class=FileResponse)
async def get_feed(
        username: str,
        format: Optional[RssFormat] = RssFormat.Atom,
        count: Optional[int] = None,
        days: Optional[int] = None,
        with_enclosures: Optional[bool] = False
):
    tg_feed = TGFeed(username)

    if days:
        after_date = datetime.date.today() - datetime.timedelta(1) * days
    else:
        after_date = None

    path = tg_gen_rss(
        feed=tg_feed,
        items=tg_feed.fetch(
            entries_count=count,
            after_date=after_date
        ),
        rss_format=format,
        use_enclosures=with_enclosures,
    )

    print(f'Generated RSS file: {path}')

    return FileResponse(
        path=path,
        media_type='text/xml'
    )

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8081
    )
