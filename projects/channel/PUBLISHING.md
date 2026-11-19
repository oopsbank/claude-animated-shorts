# Some Crazy Things: publishing log

Posting goes through the Upload-Post API (profile `somecrazythings`): YouTube, Instagram, Facebook Page.
TikTok is not on the Free plan, so it is posted by hand. Free plan: 10 uploads per month (1 per platform).

| Video | Source session | Length | File to post (captioned) | Cover | Status |
|---|---|---|---|---|---|
| The Lake That Killed 1,700 People in One Night | this session | 52.0 s | `projects/lake-nyos/final/lake-nyos_captions_1080x1920.mp4` | `projects/lake-nyos/final/thumbnail_A_eruption.jpg` | **Posted 2026-11-19**: [YouTube](https://www.youtube.com/watch?v=D4S0xpBGjJA), [Instagram](https://www.instagram.com/reel/Df6wcftE90y/), [Facebook](https://www.facebook.com/reel/1719522236283077). TikTok not yet. Cover to set by hand. |
| The Town Where You're Not Allowed to Die | Nô Lệ 1 | 55.6 s | `projects/no-dying-town/final/no-dying-town_captioned_cover_1080x1920.mp4` (cover as first 3 frames) | `projects/no-dying-town/final/no-dying-town_thumb.png` | **Not posted** |
| What If Your Plane's Windscreen Blew Out? (BA 5390) | Nô Lệ 2 (Eleven API) | 66.4 s | `shorts/windscreen/final/windscreen_subs_cover.mp4` (cover as first 3 frames) | `shorts/windscreen/final/windscreen_thumbnail.png` | **Not posted** |
| What If Night Never Came Again? | this session | 62.6 s | `projects/what-if-no-night/final/what-if-no-night_captions_1080x1920.mp4` (cover as first 3 frames) | `projects/what-if-no-night/final/thumbnail.jpg` | **Not posted** |
| What if you drank too much water? | this session | 55.3 s | `projects/too-much-water/final/too-much-water_captions_1080x1920.mp4` | `projects/too-much-water/final/thumbnail_A_glass.jpg` | Unknown (not posted through the API) |
| Beer flood | earlier session | | `shorts/beer-flood/final/beer_flood_final_subs.mp4` | `shorts/beer-flood/final/beer_flood_thumbnail.png` | Unknown (not posted through the API) |

## Notes
- Facebook caption is cut at 255 bytes: keep it short.
- From the next video on: put the cover as the first frame (0.1 s) and try sending the cover through the API.
- TikTok and Snapchat pay only for videos over 1 minute: aim for 61 to 70 s.
