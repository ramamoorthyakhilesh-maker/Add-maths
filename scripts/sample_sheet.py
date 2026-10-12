"""Render one card per topic and level into one contact sheet, to eyeball every topic.
Usage: python scripts/sample_sheet.py  ->  plots/sample_sheet_<level>.png
"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen, render
from PIL import Image
for lv in ("easy", "medium", "hard"):
    imgs = []
    for t in gen.GEN:
        out = os.path.join(ROOT, "plots", f"_s_{t}_{lv}.png")
        q = gen.build(f"{t}-{lv}-4242")
        render.draw_card(q["question"], render.topic_title(q, gen), lv, q["id"], out)
        imgs.append(Image.open(out))
    cols = 3
    rows = [imgs[i:i + cols] for i in range(0, len(imgs), cols)]
    w = max(i.width for i in imgs); sheet_h = sum(max(i.height for i in r) for r in rows)
    sheet = Image.new("RGB", (w * cols, sheet_h), "white"); y = 0
    for r in rows:
        for k, im in enumerate(r): sheet.paste(im, (k * w, y))
        y += max(i.height for i in r)
    sheet.save(os.path.join(ROOT, "plots", f"sample_sheet_{lv}.png")); print("wrote", f"sample_sheet_{lv}.png", sheet.size)
    for t in gen.GEN: os.remove(os.path.join(ROOT, "plots", f"_s_{t}_{lv}.png"))
