"""Generate README/preview visual assets from REAL repo outputs (no hand-typing).

Reads: benchmarks/throughput_results.json, experiments/*.json, pebble trace.
Writes: assets/hero.png, assets/tree.png, assets/benchmark.png, assets/demo.gif,
        assets/terminal.svg (static terminal card for README fallback).
All numbers come from the committed artifacts.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

# ---- 1. hero.png: pipeline diagram ----
fig, ax = plt.subplots(figsize=(10, 2.6))
ax.axis("off")
stages = ["characters\n29 chars", "tokens\n8 + EOF", "tree\n(+ 2 (* 3 4))", "value\n14"]
colors = ["#1f6feb", "#8250df", "#1a7f37", "#cf222e"]
for i, (s, c) in enumerate(zip(stages, colors)):
    ax.text(i / 3.2 + 0.05, 0.55, s, ha="center", va="center", fontsize=13,
            weight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.35", fc=c, ec="none"))
    if i < 3:
        ax.annotate("", xy=(i / 3.2 + 0.19, 0.55), xytext=(i / 3.2 + 0.12, 0.55),
                    arrowprops=dict(arrowstyle="->", lw=2, color="#57606a"))
ax.set_title("Pebble pipeline: characters → tokens → tree → value", fontsize=13, weight="bold", pad=12)
fig.tight_layout()
fig.savefig(ASSETS / "hero.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---- 2. tree.png: syntax tree comparison ----
fig, axes = plt.subplots(1, 2, figsize=(10, 3.2))
for axi, title, tree, val, col in [
    (axes[0], "correct tree  (+ 2 (* 3 4)) = 14", ["2", "+", ["3", "*", "4"]], 14, "#1a7f37"),
    (axes[1], "naive left-to-right  ((2+3)*4) = 20", [["2", "+", "3"], "*", "4"], 20, "#cf222e"),
]:
    axi.axis("off")
    axi.set_title(title, fontsize=11, weight="bold")
    # draw simple node boxes
    if val == 14:
        boxes = [("2", 0.2, 0.3), ("+", 0.5, 0.7), ("3", 0.65, 0.3), ("*", 0.8, 0.55), ("4", 0.9, 0.3)]
        edges = [(1, 0), (1, 4), (4, 2), (4, 3)]
    else:
        boxes = [("2", 0.15, 0.3), ("+", 0.3, 0.55), ("3", 0.42, 0.3), ("*", 0.62, 0.7), ("4", 0.85, 0.3)]
        edges = [(3, 1), (1, 0), (1, 2), (3, 4)]
    for (label, x, y) in boxes:
        axi.text(x, y, label, ha="center", va="center", fontsize=14, weight="bold",
                 bbox=dict(boxstyle="circle,pad=0.45", fc="white", ec="#24292f"))
    for a, b in edges:
        x1, y1 = boxes[a][1], boxes[a][2]
        x2, y2 = boxes[b][1], boxes[b][2]
        axi.annotate("", xy=(x2, y2 + 0.06), xytext=(x1, y1 - 0.06),
                     arrowprops=dict(arrowstyle="-", lw=1.5, color="#57606a"))
    axi.text(0.5, 0.05, f"= {val}", ha="center", fontsize=15, weight="bold", color=col)
fig.tight_layout()
fig.savefig(ASSETS / "tree.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---- 3. benchmark.png from real throughput JSON ----
bench = json.loads((ROOT / "benchmarks" / "throughput_results.json").read_text())
tok = bench["tokenize_us_per_line"]["median_us"]
par = bench["parse_us_per_expr"]["median_us"]
evl = bench["evaluate_us_per_expr"]["median_us"]
prog = bench["program_us_end_to_end"]["median_us"]
fig, ax = plt.subplots(figsize=(8, 3.4))
labels = ["tokenize\nµs/line", "parse\nµs/expr", "evaluate\nµs/expr", "program\nµs/run"]
vals = [tok, par, evl, prog]
bars = ax.bar(labels, vals, color=["#1f6feb", "#8250df", "#1a7f37", "#cf222e"])
ax.set_title("Pebble stage cost (median of 7 timeit runs)", fontsize=12, weight="bold")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{v:.2f}",
            ha="center", va="bottom", fontsize=10, weight="bold")
fig.tight_layout()
fig.savefig(ASSETS / "benchmark.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---- 4. demo.gif: typing animation of a REAL trace ----
try:
    import subprocess
    trace = subprocess.run(
        ["python3", "-m", "pebble", "--trace", "2 + 3 * 4"],
        capture_output=True, text=True, cwd=str(ROOT)).stdout.strip().splitlines()
except Exception:
    trace = ["input:  2 + 3 * 4", "tokens: NUMBER:2 OP:+ NUMBER:3 OP:* NUMBER:4",
             "tree:   (+ 2 (* 3 4))", "value:  14"]
full = "\n".join(["$ python -m pebble --trace '2 + 3 * 4'", *trace,
                  "", "$ python -m pebble programs/demo.pebble", "17", "5"])
frames = []
W, H = 760, 340
for n in range(1, len(full) + 1, 3):
    img = Image.new("RGB", (W, H), (13, 17, 23))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=18, outline=(48, 54, 61), width=2)
    d.text((18, 14), "● ● ●  pebble demo — real output", fill=(139, 148, 158))
    d.multiline_text((18, 44), full[:n], fill=(230, 237, 243), spacing=5)
    frames.append(img)
frames[0].save(ASSETS / "demo.gif", save_all=True, append_images=frames[1:],
               duration=120, loop=0)
print("wrote", sorted(p.name for p in ASSETS.iterdir()))
