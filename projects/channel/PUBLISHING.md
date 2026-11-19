# Some Crazy Things: publishing log

Posting goes through the Upload-Post API (profile `somecrazythings`): YouTube, Instagram, Facebook Page.
TikTok is not on the Free plan, so it is posted by hand. Free plan: 10 uploads per month (1 per platform).

| Video | Source session | Length | File to post (captioned) | Cover | Status |
|---|---|---|---|---|---|
| The Lake That Killed 1,700 People in One Night | this session | 52.1 s | `projects/lake-nyos/final/lake-nyos_captions_cover_1080x1920.mp4` (cover as first 3 frames; the posted copy has no cover frame) | `projects/lake-nyos/final/thumbnail_A_eruption.jpg` | **Posted 2026-11-19**: [YouTube](https://www.youtube.com/watch?v=D4S0xpBGjJA), [Instagram](https://www.instagram.com/reel/Df6wcftE90y/), [Facebook](https://www.facebook.com/reel/1719522236283077). TikTok not yet. Video file removed from the repo (in git history). |
| The Town Where You're Not Allowed to Die | Nô Lệ 1 | 55.6 s | `projects/no-dying-town/final/no-dying-town_captioned_cover_1080x1920.mp4` (cover as first 3 frames) | `projects/no-dying-town/final/no-dying-town_thumb.png` | **Posted 2026-11-19**: [YouTube](https://www.youtube.com/watch?v=xoP6jQM2UKI), [Instagram](https://www.instagram.com/reel/Df7k-OuDixI/), [Facebook](https://www.facebook.com/reel/1071526079238998). TikTok not yet. Cover sent through the API (YouTube applies it after processing). |
| What If Your Plane's Windscreen Blew Out? (BA 5390) | Nô Lệ 2 (Eleven API) | 66.4 s | `shorts/windscreen/final/windscreen_subs_cover.mp4` (cover as first 3 frames) | `shorts/windscreen/final/windscreen_thumbnail.png` | **Not posted** |
| What If Night Never Came Again? | this session | 62.6 s | `projects/what-if-no-night/final/what-if-no-night_captions_cover_1080x1920.mp4` (cover as first 3 frames) | `projects/what-if-no-night/final/thumbnail.jpg` | **Not posted** |
| What If You Could Pause Time, But Only You Got Older? | Nô Lệ 2 | 64.7 s | `shorts/what-if-pause-time/final/pause_time_final_subs.mp4` (cover as first 3 frames) | `shorts/what-if-pause-time/final/pause_time_thumbnail.png` | **Not posted** |
| What if you drank too much water? | this session | 55.4 s | `projects/too-much-water/final/too-much-water_captions_cover_1080x1920.mp4` (cover as first 3 frames) | `projects/too-much-water/final/thumbnail_A_glass.jpg` | **Posted** (by hand). Video file removed from the repo (in git history) |
| Beer flood | earlier session | 65.0 s | `shorts/beer-flood/final/beer_flood_subs_cover.mp4` (cover as first 3 frames) | `shorts/beer-flood/final/beer_flood_thumbnail.png` | **Posted** (by hand). Video file removed from the repo (in git history) |

## Notes
- Facebook caption is cut at 255 bytes: keep it short.
- Only the captioned cut with the cover as the first 3 frames (0.1 s) is kept for every video.
- Cover through the API: send `thumbnail=@file` with the upload (works for YouTube Shorts; set after processing).
- TikTok and Snapchat pay only for videos over 1 minute: aim for 61 to 70 s.
