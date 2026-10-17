---
name: video-edit
description: Edit the brand's videos end to end from raw footage - 9:16 short-form (Reels / TikTok / Shorts / ads / UGC / talking-head) and 16:9 landscape (YouTube). Finds footage and B-roll in the brand's Google Drive library, transcribes with ElevenLabs, picks the cuts, grades, frames, captions, adds music and SFX, renders a preview for review and the final on approval. Use whenever someone asks to edit, cut, re-cut, tweak or render a video, ad, reel, TikTok or short, to find B-roll ("find me a shot of..."), to index the footage library, or to export the final. Not for general coding work.
---

# Video edit

Settings live in `~/.ai-video-editor/config.json` (read it first; never print `elevenlabs_api_key`). Footage is in the
shared Google Drive library (`footage_dir`, mounted on this computer by Google Drive for Desktop). Each edit gets its own
local **project folder** in `projects_dir`; the clips it needs are copied in from Drive, so nothing heavy is written back
to the shared Drive. Finals go to `output_dir`. Music is in `music_dir`, SFX in `sfx_dir`.

**If the config file is missing or a script fails because ffmpeg/Python/a key is missing, stop and follow the
`editor-setup` skill** instead of trying to install things ad hoc.

Before cutting anything, read the **brand file** (`brand_file` in the config - the brand's rules: product facts,
approved claims, tone, ad structure, CTA, colours) and `references/style.md` (how the edit should feel). The brand file
wins where they disagree. If `brand_file` is empty, say so and ask the editor before making claims about the product.
Worked example: `references/example_edl_short.py`.

## Running the scripts

The scripts are in `scripts/` next to this file. Run them with:
- `VLOG_DIR` = the project folder, and `PYTHONPATH` = this skill's `scripts/` folder
- `python` on Windows, `python3` on Mac (if `python3` isn't the editor's own yet - right after setup, before the app
  restarts - use `~/.ai-video-editor/bin/python3`)
- the working directory = `scripts/` (edl.py lives in the project's `Edit/_work/` and is run by path)
- set env vars the way your shell does: bash `VLOG_DIR="..." PYTHONPATH="..." python prep.py`; PowerShell
  `$env:VLOG_DIR="..."; $env:PYTHONPATH="..."; python prep.py`
- prep.py needs internet (ElevenLabs). If a sandbox blocks network or writes outside the workspace, ask the editor to
  allow it rather than working around it.

Small working files go to `<project>/Edit/_work/`, heavy renders to a local cache, previews to
`<project>/Edit/Previews/`. Clip keys: DJI -> `"0047"`, Blackmagic -> `"C048"`, anything else -> file stem.
The video encoder is picked automatically (NVIDIA / AMD / Intel / Apple / software); `python enc.py` says which.

## Workflow

Tell the editor what you're doing and roughly how long each wait is.

**First video on this computer: ask where finished videos go.** If `output_dir` in the config is empty (or the folder
no longer exists), ask once, in plain words, together with your first question about the video: "Where should I put
finished videos?" Suggest a folder in their Google Drive next to the footage (e.g. a `Finished videos` folder inside
`footage_dir`, so the whole team sees them), or a folder on this computer. Save their answer with
`python settings.py output_dir "<folder>"` (a folder name alone is created inside `footage_dir`) and confirm in one
line. Never ask again once it's set; they can change it any time by asking ("put finished videos in ...").

0. **Gather footage.** Ask what the video is (product ad, UGC testimonial, talking head, YouTube) and which shoot.
   Find clips with `python library.py find <words>` (index of the Drive library; `scan` first if it's empty or stale,
   `scan "<subfolder>" --thumbs` to get thumbnail strips you can Read and then `tag`). Create
   `<projects_dir>/<Edit name>/` and copy only the clips this edit needs into it - transcription costs ElevenLabs
   credits per minute. B-roll goes in the same folder.
1. **Prep** (`FORMAT=short python prep.py` for 9:16, `FORMAT=vlog python prep.py` for 16:9): per-clip audio, contact
   sheets (`_work/sheets/`), ElevenLabs transcript (`_work/transcript.txt`, word timings `_work/t_el.json`), frame
   rate + format (`_work/meta.json`), and for 9:16 the speaker's position in each landscape clip (`_work/centers.json`).
   Prep warns on mixed frame rates; the plan uses the most common.
2. **Log** (lots of B-roll or long footage): read the contact sheets (in parallel subagents if you can) and write shot logs (location,
   GREAT/GOOD/UNUSABLE ranges, product shots, reactions, hooks). Talking-head pieces: the transcript is enough.
3. **Cut list**: write `_work/edl.py` from the example. `python words.py <clip>:<from>-<to>` for exact word times;
   `REVIEW=1 python "<project>/Edit/_work/edl.py"` prints every cut's actual text - read it all, fix clipped words and
   stray fragments (`hard_start` / `hard_end`). Set `rx=` on a cut if auto-centring framed it badly. Extras:
   `emph("word", style="serif")` accent words, `cap(..., "chip", "A > B > C")` flow pills,
   `cap(..., "img", "<path>")` screenshot / product cards, `T(..., over=(clip, t))` voice-over on B-roll.
4. **Music**: `python music.py "<track>"` for beat period and drops; drops go on hard cuts via `cue(..., sync=...)`.
5. **Preview** (seconds for a short, a few minutes for 16:9):
   `PREVIEW=1 python render.py` -> `python captions.py` -> `PREVIEW=1 python mix.py` -> `PREVIEW=1 python master.py`
   -> `Edit/Previews/<name>_preview_r<N>.mp4` + `.edits.json` + `.words.json`. Spot-check with
   `PREVIEW=1 python still.py out.jpg <t1> <t2> ...` and Read the image. Then hand it over with the `video-review`
   skill (review screen, timestamped notes). Summarise what's in, what you cut and why, and anything to check (names,
   claims, music licensing).
6. **Changes**: edit `edl.py`, rebuild, rerun step 5 (a new round). Unchanged cuts are skipped automatically.
7. **Final, only after approval**: `python render.py` -> `python mix.py` -> `python master.py` (captions are shared).
   The final goes to `output_dir`; master.py refuses to run until one is chosen (see above). Tell them where it is.
   Short ~1-2 min; 4K landscape can take 30+ min on a laptop - offer 1080p/1440p. Chain in one background command.

## Content rules

- Follow the brand file - only use claims it approves, and never make medical or health claims it doesn't allow.
- **Slurs never make the cut.** `edl_lib` cuts any flagged word inside a cut and lists it under `REMOVED WORDS`; word
  captions skip them too. Extend `BAD` in `edl_lib.py` if needed.
- Keep what sells (the product benefit, the reaction, proof, the CTA) and the genuine moments; drop dead air,
  retakes, camera fiddling. For repeated takes keep the best complete one, usually the last.
- Don't caption names or product names unless you're sure of the spelling.

## Gotchas

- Frame rate comes from the footage (`meta.json`); never assume 29.97.
- A clip that's still "online only" in Google Drive downloads on first read - copying it into the project can take a
  while on big files. Say so instead of looking stuck.
- Vertical source clips in a 16:9 edit need special framing - avoid or ask.
- Events bind to the most recent cut of that clip; `WARN anchor ... dropped` means the time isn't inside a cut.
- Music: only use tracks from `music_dir` (licensed for the brand). Say which tracks you used.
