"""hero video: the broadcast fast-forwarding with d1-2B's label per frame and a phase timeline filling in."""
import json, subprocess
from PIL import Image, ImageDraw, ImageFont
R = [json.loads(l) for l in open("out/frames.jsonl")]
N = len(R); W, H = 1280, 1000; FY = 120
F = lambda w, s: ImageFont.truetype(f"fonts/Inter-{w}.ttf", s)
BG, INK, MUT = (11, 13, 18), (240, 242, 245), (130, 136, 148)
COL = {"liftoff": (255, 92, 56), "ascent": (255, 160, 40), "onboard": (255, 214, 64), "pad": (70, 140, 255), "crew": (64, 200, 140),
       "control": (160, 110, 255), "crowd": (40, 200, 220), "studio": (110, 116, 128), "interview": (150, 156, 168),
       "graphic": (215, 100, 200), "other": (58, 62, 72)}
NAME = {"liftoff": "LIFTOFF", "ascent": "ASCENT", "onboard": "ONBOARD CAMERA", "pad": "ROCKET ON THE PAD", "crew": "THE CREW",
        "control": "LAUNCH CONTROL", "crowd": "CROWD", "studio": "STUDIO", "interview": "INTERVIEW", "graphic": "GRAPHIC", "other": "OTHER"}
TX0, TX1, TY, TH = 40, 1240, 930, 44
strip = Image.new("RGB", (TX1 - TX0, TH))
sd = ImageDraw.Draw(strip)
for i, r in enumerate(R):
    x = int(i / N * (TX1 - TX0)); sd.line([(x, 0), (x, TH)], fill=COL[r["phase"]])
fmt = lambda t: f"{t//3600}:{t%3600//60:02d}:{t%60:02d}"
LIFT = 5 * 3600 + 37 * 60 + 8
def step(t):
    if LIFT - 40 <= t <= LIFT + 150: return 1
    if LIFT - 240 <= t <= LIFT + 400: return 3
    return 12
sched, i = [], 0
while i < N: sched.append(i); i += step(R[i]["t"])
sched = [0] * 30 + sched + [-1] * 105
ASC = next(k for k, q in enumerate(R) if q["t"] >= LIFT + 40)
def frame(i, end=False):
    if i == -1: i, end = ASC, True
    r = R[i]; im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((40, 26), "6 hours of the Artemis II launch broadcast", font=F("ExtraBold", 38), fill=INK)
    d.text((40, 74), "every frame (1 per 2 s) labelled by d1-2B, a 2B model, on one RTX 3060", font=F("Regular", 24), fill=MUT)
    im.paste(Image.open(f"kf720/{i+1:05d}.jpg").convert("RGB"), (0, FY))
    c = COL[r["phase"]]
    if end:
        d.text((40, 850), f"liftoff found at {fmt(LIFT)}", font=F("ExtraBold", 34), fill=COL["liftoff"])
        msg = f"{N:,} frames in ~14 min · 2B model · one RTX 3060"
        d.text((TX1 - d.textlength(msg, font=F("SemiBold", 24)), 858), msg, font=F("SemiBold", 24), fill=MUT)
    else:
      d.rounded_rectangle([40, 860, 40 + 22, 860 + 22], 5, fill=c)
    if not end: d.text((76, 850), NAME[r["phase"]], font=F("ExtraBold", 34), fill=c)
    if not end: d.text((76 + d.textlength(NAME[r["phase"]], font=F("ExtraBold", 34)) + 18, 858), f"{r['p']:.0%} sure", font=F("SemiBold", 24), fill=MUT)
    right = "" if end else f"{fmt(r['t'])} / {fmt(R[-1]['t'])}   ·   frame {i+1:,} / {N:,}"
    d.text((TX1 - d.textlength(right, font=F("SemiBold", 24)), 858), right, font=F("SemiBold", 24), fill=MUT)
    d.rectangle([TX0, TY, TX1, TY + TH], fill=(28, 31, 38))
    px = (TX1 - TX0) if end else int((i + 1) / N * (TX1 - TX0))
    im.paste(strip.crop((0, 0, px, TH)), (TX0, TY))
    d.line([(TX0 + px, TY - 6), (TX0 + px, TY + TH + 6)], fill=INK, width=3)
    if end:
        lx = TX0 + int(next(k for k, q in enumerate(R) if q["t"] >= LIFT) / N * (TX1 - TX0))
        d.line([(lx, TY - 14), (lx, TY + TH)], fill=COL["liftoff"], width=4)
    return im
p = subprocess.Popen(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30",
                      "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "out/hero.mp4"], stdin=subprocess.PIPE)
for k, i in enumerate(sched):
    p.stdin.write(frame(i).tobytes())
p.stdin.close(); p.wait()
frame(-1).save("out/hero_last.png"); frame(next(k for k, q in enumerate(R) if q["t"] >= LIFT + 40)).save("out/hero_ascent.png")
print(len(sched), "frames,", round(len(sched) / 30, 1), "s")
