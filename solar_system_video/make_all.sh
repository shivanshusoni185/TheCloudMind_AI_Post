#!/usr/bin/env bash
# Rebuild everything from source: narration -> timeline/SRT -> frames -> audio -> mux -> QA
set -euo pipefail
cd "$(dirname "$0")/src"
python3 make_voiceover.py          # Hindi TTS per scene (+ word timings)
python3 timeline.py                # scene lengths from measured audio, SRT, full VO track
python3 render.py full "${WORKERS:-4}"   # captioned + clean video
python3 audio.py                   # score, SFX, ducking, -14 LUFS mix
cd ..
mkdir -p output
B=build
ffmpeg -y -loglevel error -i $B/video_capt.mp4  -i $B/mix_final.wav -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 14M -maxrate 18M -bufsize 28M -pix_fmt yuv420p -profile:v high -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest output/Solar_System_Final.mp4
ffmpeg -y -loglevel error -i $B/video_clean.mp4 -i $B/mix_final.wav -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 14M -maxrate 18M -bufsize 28M -pix_fmt yuv420p -profile:v high -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest output/Solar_System_Clean_Master_NoSubtitles.mp4
cp $B/vo_full.wav output/Hindi_Voiceover.wav
cp $B/Hindi_Subtitles.srt output/Hindi_Subtitles.srt
mkdir -p output/stems && cp $B/stem_narration.wav $B/stem_music.wav $B/stem_sfx.wav output/stems/
python3 src/qa.py
