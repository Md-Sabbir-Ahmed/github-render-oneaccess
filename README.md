# One Access reels: cloud render

This repo renders One Access reels on GitHub's computers. Your PC can be off.
Each folder in `exams/` is one finished HyperFrames video project (scenes, voice, fonts, sound effects).

| No. | Folder | Video | Length |
|---|---|---|---|
| 1 | `01-rickshaw-meter` | রিকশা মিটার · Tanvir the ride-app developer, Claude Max API credit, One Access | 1:09, 1080 x 1350 (4:5) |

## Render
1. Push this folder to a GitHub repo (private is fine).
2. Open the **Actions** tab, choose **Render videos**, then **Run workflow**.
3. Inputs:
   - **exams:** `all` (or `1` for one video).
   - **bitrate:** `6M`, the default.
   - **skip_done:** leave it ticked. Videos already in the release are skipped.
4. A 70 second reel takes a few minutes.

## Watch progress
- **Dashboard:** switch to the **`status`** branch and open **STATUS.md**.
- **Live logs:** **Actions** tab, the run, then a job.

## Get the video
**Releases → Rendered videos** → `01-rickshaw-meter.mp4`.

## Put in the real logo
Save the One Access logo as a square PNG at `exams/01-rickshaw-meter/assets/img/logo.png`, then rebuild:

```
cd exams/01-rickshaw-meter
python -I -X utf8 build/build.py
```

Until that file exists the video uses a placeholder mark. Brand colours are `brand_primary` and `brand_accent` in `build/script.json`.

## Change the script or make a new reel
- `build/script.json`: one line per shot. `vo` is what the voice says (numbers in words), `cap` is the caption (`*word*` turns yellow), `scene` picks the picture.
- `build/tts.py`: voices new or edited lines with ElevenLabs (Rakib). Set `ELEVENLABS_API_KEY` in the terminal first. Unchanged lines are skipped and cost nothing.
- `build/build.py`: writes `compositions/`, `index.html` and `job.json` from the script and the voice timings.
- New reel: copy the folder to `exams/02-<name>`, edit the script, run `tts.py` then `build.py`, add its `job.json` entry to `exams.json` with `"n": 2`.

## Notes
- The API key is never stored in this repo.
- Fonts (Anek Bangla, Noto Sans Bengali) are OFL. HyperFrames is Apache-2.0. GSAP is free for commercial use.
