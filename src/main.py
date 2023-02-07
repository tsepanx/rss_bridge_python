import datetime
import functools
import os
from typing import Optional, Sequence

import fastapi
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from src.base import ApiChannel, Item
from src.rss import channel_gen_rss
from src.tg_api import TGApiChannel
from src.utils import RssBridgeType, RssFormat, HTTP_HOST, HTTP_PORT
from src.yt_api import YTApiChannel

app = FastAPI()


def raise_proper_http(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{e}"
            )

        return result

    return wrapper


@app.get("/rss-feed/{username}", response_class=FileResponse)
@raise_proper_http
async def get_feed(
    username: str,
    bridge_type: RssBridgeType = RssBridgeType.TG,
    format: Optional[RssFormat] = RssFormat.ATOM,
    count: int | None = None,
    requests: int | None = None,
    days: int | None = None,
    with_enclosures: bool | None = False,
):
    channel_class: type[ApiChannel]
    if bridge_type is RssBridgeType.TG:
        channel_class = TGApiChannel
    elif bridge_type is RssBridgeType.YT:
        channel_class = YTApiChannel
    else:
        raise HTTPException(
            status_code=fastapi.status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Unknown bridge_type",
        )

    channel = channel_class(username)

    after_date = datetime.date.today() - datetime.timedelta(1) * days if days else None
    items: Sequence[Item] = channel.fetch_items(
        entries_count=count, max_requests=requests, after_date=after_date
    )

    path = channel_gen_rss(
        channel=channel,
        items=items,
        rss_format=format,
        use_enclosures=with_enclosures,
    )

    print(f"Generated RSS file: {path}")

    return FileResponse(path=path, media_type="text/xml")


if __name__ == "__main__":
    uvicorn.run(app=app, host=HTTP_HOST, port=HTTP_PORT)
