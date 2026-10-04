# SOLAR SYSTEM — आठ ग्रह, आठ अनोखी दुनिया

A roughly 3-minute (3:12) vertical motion-graphics film (1080×1920, 30 fps) with Hindi narration, synchronised Hindi subtitles, an original score and sound effects. It was built entirely from code, following `Solar_System_Motion_Graphics_Complete_Kit.txt`.

## Deliverables (`output/`)
| File | What |
|---|---|
| `Solar_System_Final.mp4` | Final film: H.264 High, 14 Mb/s, AAC 48 kHz, burned-in Hindi subtitles |
| `Solar_System_Clean_Master_NoSubtitles.mp4` | Same film without subtitles (titles/fact cards kept) |
| `Hindi_Voiceover.wav` | Full-length narration on the final timeline (48 kHz mono) |
| `Hindi_Subtitles.srt` | Subtitles timed from the TTS word boundaries |
| `stems/` | Separate narration, music and SFX stems (48 kHz stereo) |

The MP4s are larger than GitHub's 100 MB file limit, so they are git-ignored. Rebuild them with `./make_all.sh`, or take them from the session hand-off.

## Pipeline (`src/`) — every step is editable code
1. `script_data.py` holds the exact Hindi narration for the 11 scenes. Edit the copy here.
2. `make_voiceover.py` synthesises the narration with Microsoft Edge neural TTS (`hi-IN-MadhurNeural`, +12% rate) and saves per-word timings.
3. `timeline.py` builds the edit timeline from the **measured** narration (lead-in/hold per scene), then writes the SRT and the full VO track.
4. `scenes.py` contains the 11 scenes. All titles, numbers, fact chips, diagrams and captions are overlays drawn here, and their reveals are keyed to narration words via `kw(scene, word)`.
5. `planet.py` is the renderer: ray-cast textured spheres, one consistent sunlight direction, atmospheres, Earth clouds/night lights/ocean glint, Saturn and Uranus rings in the equatorial plane with ring↔planet shadows, the Sun with granulation and a prominence, a parallax starfield and a procedural Pluto.
6. `render.py` renders frames in parallel and writes the captioned and clean videos. `python render.py stills 12.5 40` writes review stills.
7. `audio.py` produces the original synthesized score (D major, 88 BPM, following the brief's music arc), editorial SFX at event times, music ducking under speech, and two-pass loudnorm to −14 LUFS / −1.5 dBTP.
8. `qa.py` runs the automated review: specs, frame count, black/frozen frames, A/V sync, loudness, subtitle text versus script, planet order, and on-screen copy versus the brief.

Requirements: Python 3.11, `numpy scipy pillow(raqm) edge-tts fonttools`, ffmpeg, and Noto Sans / Noto Sans Devanagari / DejaVu Sans fonts.

## Science notes applied
- Pluto is labelled as a dwarf planet.
- Orbit maps say "Illustrative scale".
- The Jupiter–Earth inset uses true equatorial-diameter proportions (142,984 : 12,756 km).
- Uranus's 98° axis is measured from the orbital normal.
- The Kuiper Belt continues off-frame beyond Neptune.
- The asteroid belt sits between Mars and Jupiter.
- Neptune's winds and Mars's water are labelled as illustrations.
- Venus is shown cloud-covered (no surface visible).
- Earth's 71/29 split is a separate bar chart.

## Credits
- Planet textures: Solar System Scope (solarsystemscope.com), **CC BY 4.0**, based on NASA data. Pluto's texture is procedural.
- Voice: Microsoft Edge neural TTS (hi-IN-MadhurNeural). Check the TTS terms for your publishing use, or replace `build/vo/*.wav` with a human recording and re-run from step 3.
- Music and SFX: original, procedurally synthesised in `audio.py`.
- Facts: NASA (see the brief's source list).
