#!/usr/bin/env bash
# download the broadcast and cut keyframes (1 every 2 s)
set -e
mkdir -p video kf kf720 out
yt-dlp -f "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]" --merge-output-format mp4 \
  -o "video/artemis2-launch.%(ext)s" "https://www.youtube.com/watch?v=Tf_UjBMIzNo"
ffmpeg -hide_banner -v error -nostdin -i video/artemis2-launch.mp4 -vf "fps=1/2,scale=640:360" -q:v 3 kf/%05d.jpg   # what the model sees
ffmpeg -hide_banner -v error -nostdin -i video/artemis2-launch.mp4 -vf "fps=1/2" -q:v 2 kf720/%05d.jpg              # for the video render
ls kf | wc -l
