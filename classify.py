"""ask d1-2B about every keyframe of the artemis II launch broadcast.
usage: python3 classify.py <workers> [limit] [out.jsonl]
server: D1_URLS (comma separated), default http://127.0.0.1:8080"""
import base64, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import itertools, os, threading
URLS = os.environ.get("D1_URLS", "http://127.0.0.1:8080").split(",")
_rr = itertools.cycle(URLS); _lk = threading.Lock()
def api():
    with _lk: return f"{next(_rr).rstrip('/')}/v1/systemone"
KF = Path("kf")
STATE = "One frame from NASA's live broadcast of the Artemis II launch."
PHASES = {
    "studio": "Hosts or commentators talking to the camera, in a studio or at a desk",
    "interview": "One person being interviewed or speaking, head and shoulders shot",
    "crew": "The astronauts in orange suits: suiting up, walking out, waving, riding the van or boarding",
    "pad": "The rocket standing on the launch pad, no engine fire",
    "control": "A launch or mission control room with consoles and screens",
    "liftoff": "The rocket lifting off the pad with huge engine flames and smoke",
    "ascent": "The rocket flying up into the sky with a bright exhaust plume",
    "onboard": "A camera on the rocket: looking down at the Earth or at parts separating",
    "crowd": "Spectators or crowds watching outdoors",
    "graphic": "A computer animation, diagram, countdown clock or text graphic",
    "other": "Anything else",
}
QUESTIONS = {"phase": {"type": "choice", "instructions": "What does this frame show?", "criteria": PHASES}}
EPIC = {"liftoff", "ascent", "onboard"}

def ask(p):
    img = "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()
    body = json.dumps({"state": STATE, "images": [img], "questions": QUESTIONS}).encode()
    for _ in range(4):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(api(), body, {"Content-Type": "application/json"}), timeout=600))
            a = r["answers"]
            ph = a["phase"]
            return {"t": (int(p.stem) - 1) * 2, "phase": ph["choice"], "p": round(ph["confidence"], 3),
                    "probs": {k: round(v, 4) for k, v in ph["probabilities"].items()}, "tok": r["usage"]["input_tokens"]}
        except Exception as e:
            err = e
    return {"t": (int(p.stem) - 1) * 2, "error": str(err)}

if __name__ == "__main__":
    workers = int(sys.argv[1]); limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    frames = sorted(KF.glob("*.jpg"))
    if limit: frames = frames[:: max(1, len(frames) // limit)][:limit]
    ask(frames[0])  # warm
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(ask, frames))
    dt = time.time() - t0
    errs = sum("error" in r for r in res)
    if out: out.write_text("\n".join(json.dumps(r) for r in res) + "\n")
    print(json.dumps({"workers": workers, "frames": len(res), "sec": round(dt, 1), "fps": round(len(res) / dt, 1), "errors": errs,
                      "tok": max((r.get("tok", 0) for r in res), default=0)}))
