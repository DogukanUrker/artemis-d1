"""frames.jsonl -> smoothed phase timeline + youtube chapters"""
import json, collections
R = [json.loads(l) for l in open("out/frames.jsonl")]
WIN = 45  # 90 s rolling vote, "other" only counts at half weight
def vote(i):
    c = collections.Counter()
    for r in R[max(0, i - WIN):i + WIN + 1]:
        c[r["phase"]] += 0.5 if r["phase"] == "other" else 1
    return c.most_common(1)[0][0]
S = [vote(i) for i in range(len(R))]
# segments, then merge anything under 3 min into its neighbour (launch phases stay)
seg = []
for i, s in enumerate(S):
    if seg and seg[-1][0] == s: seg[-1][2] = i
    else: seg.append([s, i, i])
KEEP = {"liftoff", "ascent", "onboard"}
changed = True
while changed:
    changed = False
    for k, (s, a, b) in enumerate(seg):
        if (b - a + 1) * 2 < 360 and s not in KEEP and len(seg) > 1:
            j = k - 1 if k > 0 else k + 1
            seg[j][1], seg[j][2] = min(seg[j][1], a), max(seg[j][2], b); del seg[k]; changed = True; break
    for k in range(len(seg) - 1, 0, -1):
        if seg[k][0] == seg[k - 1][0]: seg[k - 1][2] = seg[k][2]; del seg[k]
NAME = {"studio": "Commentary", "interview": "Interviews", "crew": "The crew", "pad": "Rocket on the pad", "control": "Launch control",
        "liftoff": "LIFTOFF", "ascent": "LIFTOFF", "onboard": "Onboard views", "crowd": "Crowds watching", "graphic": "Mission graphics", "other": "Coverage"}
fmt = lambda t: f"{t//3600}:{t%3600//60:02d}:{t%60:02d}"
lines = []
for s, a, b in seg:
    if lines and lines[-1].split(" ", 1)[1] == NAME[s]: continue
    lines.append(f"{fmt(R[a]['t'])} {NAME[s]}")
open("out/chapters.txt", "w").write("\n".join(lines) + "\n")
json.dump(S, open("out/smoothed.json", "w"))
print(len(lines), "chapters"); print("\n".join(lines))
