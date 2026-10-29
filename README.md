# artemis-d1

A 2B model watches 6 hours of NASA's Artemis II launch broadcast and labels every frame.

The model is [d1-2B](https://huggingface.co/LiquidAI/d1-2B) from Liquid AI, a decision model. It doesn't write text. You give it an image and a question with fixed options, and it returns the pick plus a probability for each option. Here the question is "what does this frame show?" with 11 options: studio, interview, crew, pad, control, liftoff, ascent, onboard, crowd, graphic, other.

The run: 11,486 frames (1 every 2 s) in about 14 minutes on one RTX 3060 12GB. It found liftoff at 5:37:08 with no human scrubbing.

`out/frames.jsonl` has every answer from that run, so you can render the video or check it without running the model.

## how it works

1. `get_video.sh` downloads the broadcast with yt-dlp and cuts one frame every 2 s with ffmpeg (640x360 for the model, 720p for the video).
2. `classify.py` sends every frame to llama-server's `/v1/systemone` endpoint with one `choice` question. One question per frame keeps it fast: every extra question makes the model read the image again.
3. `chapters.py` smooths the labels with a 90 s rolling vote and writes YouTube style chapters.
4. `render_hero.py` renders the video: the broadcast fast-forwarding with the model's label and confidence per frame, and a colored timeline that fills in. It slows down around liftoff.

## run it

You need a llama.cpp build with LFM3 d1 support (merged in late October 2026) and the GGUF from [LiquidAI/d1-2B-GGUF](https://huggingface.co/LiquidAI/d1-2B-GGUF).

```bash
llama-server -m d1-2B-Q8_0.gguf --mmproj mmproj-d1-2B-F16.gguf \
  -ngl 99 -fa on -np 1 -c 8192 -b 8192 -ub 8192 --port 8080
```

Keep `-np 1`. d1 requests don't batch across slots anyway, and with `-np > 1` some slots can get stuck forever. One slot already keeps the GPU at 100%.

```bash
./get_video.sh
python3 classify.py 3 0 out/frames.jsonl     # 3 workers keep the queue full
python3 chapters.py
# render needs pillow, ffmpeg, and Inter fonts (Inter-Regular/SemiBold/ExtraBold.ttf) in fonts/
python3 render_hero.py                       # -> out/hero.mp4
```

Point `classify.py` at another server with `D1_URLS=http://host:port`.

`render_hero.py` has the liftoff time (`LIFT`) hardcoded for this broadcast. Change it if you use another video.

## notes

The broadcast is NASA footage: https://www.youtube.com/watch?v=Tf_UjBMIzNo

Same idea, earlier: I used the older d1-3B to chapter a 6 hour Call of Duty campaign recording and to find my shocked face for thumbnails.
