[![python](https://github.com/tsepanx/rss-bridge-python/actions/workflows/main.yml/badge.svg)](https://github.com/tsepanx/rss-bridge-python/actions/workflows/main.yml)

# RSS Bridge (~~Feed aggregator~~)

### Design
For now, this project pretends to be an alternative of [rss-bridge](https://github.com/RSS-Bridge/rss-bridge),
customized for my specific needs.\
One of the main additional feature is possibility to fetch not just 20 last entries,
but filter by count and start date, or even fetch all available entries.

[//]: # (May be integrated with my other projects in the future.)

### Types of feed to implement
- [x] Youtube
  - [x] Channel metadata, videos
  - [ ] Video - parse metadata: title, preview_img, etc
  - [ ] Playlist
- [x] Telegram Channel
- Review rss feeds of these sources
  - ~~Mastodon~~ - Seems no rss available
  - Gemini - Requires additional non-http parsing

### TODO & Features to implement
- [x] Write tests
- [ ] Limit entries count by made requests
- [ ] Param for feed: whitelist/blacklist of keywords in title/text
- [ ] DB support, to cache existing `rss` files
  - Specify update interval (5min)

### Refactor
- [x] channel_gen_rss & yt_gen_rss
