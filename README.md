
# RSS Bridge (~~Feed aggregator~~)

### Design
For now, this project pretends to be an alternative of [rss-bridge](https://github.com/RSS-Bridge/rss-bridge),
customized for my specific needs.
May be integrated with my other projects in the future.

### Types of feed to implement
- [x] Youtube
  - [x] Channel metadata, videos
  - [ ] Video
  - [ ] Playlist
- [x] Telegram Channel
- Review rss feeds of these sources
  - ~~Mastodon~~ - Seems no rss available
  - Gemini - Requires additional non-http parsing

### TODO & Features to implement
- Write tests
- **Youtube**: parse single video metadata: title, preview_img, etc
- Param for feed: whitelist/blacklist of keywords in title/text
- DB support, to cache existing `rss` files
  - Specify update interval (5min)
