# Edit style

The feel to hit: authentic, fast, clean. The edit should feel invisible, not "edited". Brand specifics (colours,
CTA, claims) are in the brand file; this file is how the cut itself should feel.

## 9:16 short-form (FORMAT=short) - Reels, TikTok, Shorts, paid social

Vertical 1080x1920. Landscape footage is auto-cropped to a 9:16 column centred on the speaker.

### Pacing (the #1 thing)
- Perfect the dead space. Good UGC runs ~190 words/min with almost no gap between words. In short mode `T()` cuts
  every pause > 0.35 s *inside* a phrase automatically and pads tightly, so pick whole sentences and let the engine
  jump-cut them.
- **Hook in the first 1-2 seconds**: the strongest line, said with energy, straight into the point. No warm-up, no
  "hey guys". Open on the best line of the take even if it came later. For ads, call out the audience
  ("If you have to clock in before everyone else in the house is up...").
- Ads: if the brand file defines an ad structure, follow it. Default: hook (0-2 s) -> pain point/desire (2-3 s)
  -> show the product (4-6 s) -> USPs -> CTA. Something new on screen at least every 3 s.
- End on a clean line or the CTA; no fade (shorts loop).
- Ads: 15-30 s unless the brief says otherwise. Organic: as long as it stays interesting, usually under 60 s.

### Picture
- Every jump cut changes framing: wide (1.0) / medium (1.15) / tight (1.32), plus a small sideways shift - automatic
  when z is omitted. Use `snap@T` rarely (one comedic beat, if any).
- Natural look - light grade only (`home` daylight interiors, `out` outdoors, `eve` lamp-lit bedrooms and early mornings, `gym` dim).
- Cut to product B-roll whenever the speaker describes the product: use `over=(clip, t)` so the voice keeps going over
  the product shot. Change the shot at least every 3 s in ads.
- `rx=` on a cut if auto-centring framed it badly.

### Captions (automatic, subs.py)
- Small, clean: white semibold sans, natural case as spoken, 2-4 words per line, centred around chest height, soft
  shadow, no thick outline, no karaoke highlight, no all-caps.
- Accent 1-3 key words per video with `emph("word", style="serif")` or `style="red"` for a negation/contrast word.
  Numbers and $ amounts turn green automatically.
- Keep captions and graphics out of the bottom ~20% and right edge (platform UI covers them).

### Graphics (sparingly, only where they explain what's said)
- `cap(clip, t, dur, "chip", "Old way > Problem > Product")`: flow pills revealed left to right, top of frame.
  Good for steps, before/after, lists of 2-4 things.
- `cap(clip, t, dur, "img", "<path to png>")`: card popping in at the top - product shot, Trustpilot review, offer.
- No big titles, no timestamps, no terminal-style text.

### Sound
- Dialogue first (cleaned, -14 LUFS master). Quiet music bed ~12 dB under the voice (`db=-24`, ducks under speech).
- SFX almost never - one subtle whoosh or pop on a real moment at most.

## 16:9 landscape (FORMAT=vlog) - YouTube, longer brand videos

- Cold open with the best moment (10-20 s), then the story in order, one section per location/topic.
- Section changes: `tin="zoom"` transition on the first cut of a section (set `TRANSITION_SFX` to a whoosh from the
  SFX folder, or leave `None` for silent). ~1 per section, never between every cut.
- Captions: `stamp` lower-third to open a section ("Day 1 // unboxing"), `cap` for facts, `card` for tips worth
  screenshotting (header + rows). Word captions only if asked (`WORDCAPS=1`).
- Zooms: alternate `n`/`p` on consecutive talk cuts (automatic), `push` on B-roll, `snap@T` on a real reaction.
- Music per section, ducked ~11 dB under speech, louder for montages. Master -14 LUFS.
