"""Stress versions of three sheets: much blurrier, darker, and lower resolution than a normal phone photo.
These find the breaking point; the right behavior when unsure is to skip or flag, not guess."""
import json
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
truth = json.load(open("truth.json", encoding="utf-8"))
out = []
for sid, blur, dark, width in [(3, 2.6, 0.45, 900), (8, 1.8, 0.35, 850), (9, 2.4, 0.5, 800)]:
    im = Image.open(f"sheet-{sid:02d}.jpg").convert("RGB")
    im = im.resize((width, int(im.size[1] * width / im.size[0])), Image.LANCZOS).filter(ImageFilter.GaussianBlur(blur))
    im = ImageEnhance.Brightness(im).enhance(1 - dark)
    a = np.asarray(im, np.float32) + np.random.default_rng(sid).normal(0, 12, (im.size[1], im.size[0], 3))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(f"stress-{sid:02d}.jpg", quality=60)
    t = dict(next(x for x in truth if x["id"] == sid)); t["id"] = 100 + sid; t["file"] = f"stress-{sid:02d}.jpg"
    t["desc"] = f"STRESS: sheet {sid}, heavy blur, dark, {width}px wide"
    out.append(t)
json.dump(out, open("truth-stress.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("made", len(out))
