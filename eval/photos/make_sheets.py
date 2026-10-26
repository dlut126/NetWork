"""Generate 10 synthetic sign-up sheet photos with answer keys for testing NetWork's photo capture.
Every person, email, and company here is made up. Sheets get harder from 1 to 10.
Output: out/sheet-01.jpg ... out/sheet-10.jpg and out/truth.json
"""
import json, random, math, os, html
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
import numpy as np
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
FS = (ROOT / "node_modules/@fontsource").as_uri()
FONTS = {  # handwriting fonts, each a different "person"
    "caveat": "Caveat", "kalam": "Kalam", "indie-flower": "Indie Flower", "reenie-beanie": "Reenie Beanie",
    "homemade-apple": "Homemade Apple", "shadows-into-light": "Shadows Into Light", "nanum-pen-script": "Nanum Pen Script",
    "patrick-hand": "Patrick Hand"}
HAND = list(FONTS.values())
INKS = ["#1b2a6b", "#14161c", "#1f3fa8", "#2a2a2a", "#0b3d91"]

def P(name, firm="", email="", phone="", linkedin="", role=""):
    return {"name": name, "firm": firm, "email": email, "phone": phone, "linkedin": linkedin, "role": role}

# Each sheet: title, columns (truth keys), rows, style. A row may carry "skip": True (unreadable, should NOT be extracted)
# or "struck": True (crossed out by the writer and rewritten on the next line; should NOT be extracted).
SHEETS = [
 dict(id=1, desc="Clean printed table, good light", title="Product Management Club · Fall Mixer", cols=["name","email","firm"], printed=True,
      rows=[P("Hannah Brooks","hbrooks@gmail.com","Notion"),P("Omar Siddiqui","omar.siddiqui@anderson.ucla.edu","Amazon"),
            P("Grace Liu","grace.liu@stripe.com","Stripe"),P("Diego Ramirez","dramirez@outlook.com","Deloitte"),
            P("Priya Nair","priya.nair@salesforce.com","Salesforce"),P("Ben Carter","bcarter@meta.com","Meta"),
            P("Lauren Kim","lauren.kim@gmail.com","Figma"),P("Marcus Hill","mhill@adobe.com","Adobe")],
      tilt=0.6, blur=0.3, noise=4, dark=0.0),
 dict(id=2, desc="Neat handwriting, one writer's style per row", title="Consulting Club Coffee Chats — sign in", cols=["name","email","firm"],
      rows=[P("Ethan Walsh","ethanwalsh@gmail.com","Bain"),P("Sofia Rossi","srossi@bcg.com","BCG"),P("Kevin Tran","ktran@mckinsey.com","McKinsey"),
            P("Maya Patel","maya.p@ey.com","EY-Parthenon"),P("Jordan Lee","jordanlee22@yahoo.com","Accenture"),P("Rachel Adams","radams@kearney.com","Kearney"),
            P("Tom Becker","tbecker@oliverwyman.com","Oliver Wyman"),P("Nina Shah","nshah@lek.com","L.E.K.")],
      tilt=-2.0, blur=0.5, noise=6, dark=0.05),
 dict(id=3, desc="Mixed handwriting, tilted and photographed at an angle", title="Tech Trek Info Session", cols=["name","firm","email"],
      rows=[P("Alex Morgan","Google","amorgan@google.com"),P("Chloe Bennett","Airbnb","chloe.b@airbnb.com"),P("Raj Malhotra","Nvidia","rmalhotra@nvidia.com"),
            P("Emily Zhang","Microsoft","emzhang@microsoft.com"),P("Sam O'Connor","Uber","soconnor@uber.com"),P("Isabel Cruz","Apple","icruz@apple.com"),
            P("Derek Johnson","Snowflake","derek.johnson@snowflake.com"),P("Fatima Ali","Datadog","fali@datadoghq.com"),P("Liam Murphy","LinkedIn","lmurphy@linkedin.com"),
            P("Zoe Park","Pinterest","zpark@pinterest.com")],
      tilt=4.5, persp=0.06, blur=0.6, noise=7, dark=0.08),
 dict(id=4, desc="Blanks: some people skipped email or company", title="Healthcare Business Assoc. — Panel Night", cols=["name","firm","email"],
      rows=[P("Victoria Hayes","Kaiser Permanente","vhayes@kp.org"),P("Andre Wilson","","andrew.wilson88@gmail.com"),P("Mei Chen","Genentech",""),
            P("Carlos Mendez","",""),P("Hope","",""),P("Daniel Osei","Johnson & Johnson","dosei@its.jnj.com"),P("Laura Fischer","Medtronic","")],
      tilt=-1.2, blur=0.5, noise=6, dark=0.05),
 dict(id=5, desc="A crossed-out entry rewritten below, and one scribbled, unreadable row", title="Entertainment & Media Club Sign-Up", cols=["name","email","firm"],
      rows=[P("Jasmine Reed","jreed@netflix.com","Netflix"),
            dict(P("Tyler Grant","tgrant@disnye.com","Disney"), struck=True),P("Tyler Grant","tgrant@disney.com","Disney"),
            P("Olivia Martinez","omartinez@wbd.com","Warner Bros. Discovery"),dict(P("Xqzv Ttrrw","",""), skip=True),
            P("Noah Kim","noah.kim@spotify.com","Spotify"),P("Ava Thompson","ava.thompson@paramount.com","Paramount")],
      tilt=1.8, blur=0.6, noise=7, dark=0.06),
 dict(id=6, desc="Dim, blurry, noisy phone photo", title="Real Estate Club — Site Visit RSVP", cols=["name","email","firm"],
      rows=[P("Brandon Scott","bscott@cbre.com","CBRE"),P("Hailey Nguyen","hnguyen@jll.com","JLL"),P("Marco Bianchi","mbianchi@blackstone.com","Blackstone"),
            P("Tiffany Wu","twu@prologis.com","Prologis"),P("Josh Feldman","jfeldman@related.com","Related"),P("Kayla Brown","kbrown@hines.com","Hines")],
      tilt=-3.0, persp=0.04, blur=1.6, noise=16, dark=0.38),
 dict(id=7, desc="Different columns: company first, phone and LinkedIn", title="Fintech Club Founders Breakfast", cols=["firm","name","phone","linkedin"],
      rows=[P("Ramp","Elena Petrova",phone="(415) 555-0142",linkedin="linkedin.com/in/elenapetrova"),P("Plaid","Chris Doyle",phone="650-555-0187",linkedin="linkedin.com/in/chrisdoyle"),
            P("Chime","Aisha Bello",phone="(213) 555-0119",linkedin=""),P("Brex","Ryan Cho",phone="",linkedin="linkedin.com/in/ryancho"),
            P("Robinhood","Megan Foster",phone="310-555-0166",linkedin="linkedin.com/in/meganfoster")],
      tilt=2.2, blur=0.5, noise=6, dark=0.05),
 dict(id=8, desc="Long sheet: 20 people", title="Women in Business — Annual Kickoff", cols=["name","email","firm"],
      rows=[P(n, e, f) for n, e, f in [
        ("Abigail Turner","aturner@gmail.com","Goldman Sachs"),("Brianna Lopez","blopez@jpmorgan.com","J.P. Morgan"),("Camila Reyes","creyes@pwc.com","PwC"),
        ("Dana Whitfield","dwhitfield@kpmg.com","KPMG"),("Erin O'Neill","eoneill@nike.com","Nike"),("Fiona Grant","fgrant@loreal.com","L'Oréal"),
        ("Gabriela Santos","gsantos@pg.com","P&G"),("Heather Lin","hlin@visa.com","Visa"),("Ivy Chen","ivy.chen@gmail.com",""),
        ("Julia Novak","jnovak@tesla.com","Tesla"),("Kara Mitchell","kmitchell@hulu.com","Hulu"),("Leah Goldberg","lgoldberg@bain.com","Bain"),
        ("Monica Alvarez","malvarez@target.com","Target"),("Natalie Brooks","nbrooks@ibm.com","IBM"),("Paige Ellis","pellis@intuit.com","Intuit"),
        ("Quinn Harper","qharper@yahoo.com",""),("Riley Evans","revans@oracle.com","Oracle"),("Sara Haddad","shaddad@cisco.com","Cisco"),
        ("Tessa Morgan","tmorgan@lyft.com","Lyft"),("Uma Krishnan","ukrishnan@deloitte.com","Deloitte")]],
      tilt=-1.0, persp=0.03, blur=0.6, noise=6, dark=0.05, small=True),
 dict(id=9, desc="International names with accents", title="Global Business Club Welcome Night", cols=["name","email","firm"],
      rows=[P("José Muñoz","jmunoz@santander.com","Santander"),P("Siobhán Ní Bhriain","siobhan.nb@gmail.com","Accenture"),P("Łukasz Nowak","lnowak@allegro.pl","Allegro"),
            P("Nguyễn Thị Lan","lan.nguyen@vng.com.vn","VNG"),P("Zoë Müller","zoe.mueller@siemens.com","Siemens"),P("Aarav Gupta","aarav.gupta@infosys.com","Infosys"),
            P("Chidi Okeke","cokeke@flutterwave.com","Flutterwave"),P("Yuki Tanaka","ytanaka@sony.co.jp","Sony")],
      tilt=1.4, blur=0.5, noise=6, dark=0.05),
 dict(id=10, desc="Free-form notebook page, no table, messy", title="Marketing Assoc. — Brand Teardown (10/22)", cols=None, notebook=True,
      rows=[P("Jake Peterson","jake.p@gmail.com","Coca-Cola"),P("Ana Silva","asilva@unilever.com","Unilever"),P("Kris Patel","kris@patelstudio.co","Patel Studio"),
            P("Morgan Yates","myates@hubspot.com","HubSpot"),P("Lena Park","",""),P("Theo Russo","trusso@redbull.com","Red Bull")],
      tilt=-3.5, persp=0.07, blur=0.9, noise=10, dark=0.15),
]

# Sheets 1, 2, 5, 6, 8, 9, 10 list rows as (name, email, company); P() takes (name, company, email), so swap them back.
for _s in SHEETS:
    if _s["id"] in (1, 2, 5, 6, 8, 9, 10):
        for _r in _s["rows"]: _r["firm"], _r["email"] = _r["email"], _r["firm"]
    if _s["id"] == 7:   # listed as (company, name)
        for _r in _s["rows"]: _r["firm"], _r["name"] = _r["name"], _r["firm"]

LABEL = {"name":"Name","email":"Email","firm":"Company","phone":"Phone","linkedin":"LinkedIn"}

def font_css():
    out = []
    for slug in FONTS:
        out.append(f'<link rel="stylesheet" href="{FS}/{slug}/400.css">')
    out.append(f'<link rel="stylesheet" href="{FS}/patrick-hand/400.css">')
    return "\n".join(out)

def cell(text, font, ink, rng, extra="", colw=320):
    if not text: return f"<td></td>"
    size = rng.randint(26, 34)
    if font in ("Reenie Beanie", "Nanum Pen Script"): size += 8
    if font == "Homemade Apple": size -= 6
    k = {"Homemade Apple": 0.78, "Reenie Beanie": 0.42, "Nanum Pen Script": 0.4, "Caveat": 0.45}.get(font, 0.55)
    size = int(min(size, (colw - 30) / (k * max(len(text), 1))))   # people write smaller when the box is short
    rot = rng.uniform(-2.2, 2.2); dy = rng.uniform(-4, 4)
    return (f'<td><span style="font-family:\'{font}\';font-size:{size}px;color:{ink};display:inline-block;'
            f'transform:translateY({dy:.1f}px) rotate({rot:.1f}deg);{extra}">{html.escape(text)}</span></td>')

def sheet_html(s, rng):
    small = s.get("small")
    rowh = 46 if small else 64
    if s.get("notebook"):
        lines = []
        for i, r in enumerate(s["rows"]):
            font = rng.choice(HAND); ink = rng.choice(INKS)
            bits = [r["name"]] + [x for x in (r["email"], r["firm"]) if x]
            sep = rng.choice([" — ", " · ", "  /  ", ",  "])
            lines.append(f'<div class="nb" style="padding-left:{rng.randint(10,60)}px">{cell(sep.join(bits), font, ink, rng, colw=1500).replace("<td>","").replace("</td>","")}</div>')
        body = "\n".join(lines)
        return f"""<div class="paper notebook"><div class="hd" style="font-family:'Kalam';font-size:34px;color:#1b2a6b">{html.escape(s['title'])}</div>
          <div style="font-family:'Caveat';font-size:28px;color:#333;margin:0 0 18px 60px">sign in pls — name, email, where you work :)</div>{body}
          <div style="height:120px"></div></div>"""
    head = "".join(f"<th>{LABEL[c]}</th>" for c in s["cols"])
    trs = []
    for r in s["rows"]:
        font = rng.choice(HAND); ink = rng.choice(INKS)
        if s.get("printed"):
            tds = "".join(f'<td class="pr">{html.escape(r.get(c,""))}</td>' for c in s["cols"])
        elif r.get("skip"):
            tds = "".join(cell(x, "Homemade Apple", ink, rng, "filter:blur(3.2px);opacity:.75;font-size:22px") for x in ["Xqzv Ttrrw", "jq@???", ""][:len(s["cols"])])
        else:
            tds = "".join(cell(r.get(c, ""), font, ink, rng, colw=980 // len(s["cols"])) for c in s["cols"])
        cls = "struck" if r.get("struck") else ""
        trs.append(f'<tr class="{cls}" style="height:{rowh}px">{tds}</tr>')
    for _ in range(3 if not small else 1):
        trs.append(f'<tr style="height:{rowh}px">' + "<td></td>" * len(s["cols"]) + "</tr>")
    return f"""<div class="paper"><div class="hd">{html.escape(s['title'])}</div>
      <div class="sub">Please print clearly. We'll send the slides and follow-up info by email.</div>
      <table><thead><tr>{head}</tr></thead><tbody>{''.join(trs)}</tbody></table></div>"""

CSS = """body{margin:0;background:#fff}
.paper{width:1100px;padding:56px 60px 70px;background:#fdfcf7;box-sizing:border-box;font-family:Arial,Helvetica,sans-serif}
.hd{font:700 30px Arial;color:#222;margin-bottom:6px}.sub{font:15px Arial;color:#666;margin-bottom:22px}
table{width:100%;border-collapse:collapse;table-layout:fixed}th{font:700 16px Arial;text-align:left;padding:8px 10px;border:1.5px solid #555;background:#eee}
td{border:1.2px solid #777;padding:2px 12px;vertical-align:middle;overflow:hidden;white-space:nowrap}
td.pr{font:20px Arial;color:#111}
tr.struck td{position:relative}tr.struck td span{text-decoration:line-through;text-decoration-thickness:3px;text-decoration-color:#1b2a6b}
tr.struck td::after{content:"";position:absolute;left:4%;right:6%;top:46%;border-top:3px solid #1b2a6b;transform:rotate(-2deg)}
.notebook{background:repeating-linear-gradient(#fdfcf7 0 63px,#9bb7e0 63px 65px);border-left:4px solid #f19a9a}
.nb{height:65px;display:flex;align-items:flex-end;padding-bottom:6px}
"""

def photograph(img, s, rng):
    """Turn a flat scan into something that looks like a phone photo."""
    w, h = img.size
    pad = 160
    nrng = np.random.default_rng(s["id"])
    # table surface
    bgc = rng.choice([(122, 86, 58), (150, 140, 128), (70, 72, 80), (196, 182, 160)])
    bg = Image.new("RGB", (w + 2 * pad, h + 2 * pad), bgc)
    tex = (nrng.normal(0, 10, (h + 2 * pad, w + 2 * pad, 1)) * np.ones((1, 1, 3))).astype(np.int16)
    bg = Image.fromarray(np.clip(np.asarray(bg, np.int16) + tex, 0, 255).astype(np.uint8))
    shadow = Image.new("L", bg.size, 0); ImageDraw.Draw(shadow).rectangle([pad + 14, pad + 18, pad + w + 14, pad + h + 18], fill=120)
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    bg = Image.composite(Image.new("RGB", bg.size, (20, 20, 20)), bg, shadow)
    bg.paste(img, (pad, pad))
    img = bg.rotate(s.get("tilt", 0), resample=Image.BICUBIC, expand=False, fillcolor=bgc)
    # perspective: top edge narrower, like a phone held at an angle
    p = s.get("persp", 0)
    if p:
        W, H = img.size; d = p * W
        src = [(d, 0), (W - d * 0.6, 0), (W, H), (0, H)]
        dst = [(0, 0), (W, 0), (W, H), (0, H)]
        coeffs = _persp(dst, src)
        img = img.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC, fillcolor=bgc)
    # uneven light
    W, H = img.size
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = rng.uniform(0.2, 0.8) * W, rng.uniform(0.1, 0.5) * H
    grad = 1 - s.get("dark", 0) * (np.hypot(xx - cx, yy - cy) / np.hypot(W, H) * 2.2)
    arr = np.asarray(img, np.float32) * np.clip(grad, 0.3, 1)[..., None]
    arr += nrng.normal(0, s.get("noise", 5), arr.shape)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img = ImageEnhance.Color(img).enhance(0.92).filter(ImageFilter.GaussianBlur(s.get("blur", 0.5)))
    # crop a bit like a real photo, resize to phone-ish resolution
    W, H = img.size; c = 0.04
    img = img.crop((int(W * c), int(H * c), int(W * (1 - c)), int(H * (1 - c))))
    k = 1800 / max(img.size)
    return img.resize((int(img.size[0] * k), int(img.size[1] * k)), Image.LANCZOS)

def _persp(pa, pb):
    A = []
    for (x, y), (X, Y) in zip(pa, pb):
        A += [[x, y, 1, 0, 0, 0, -X * x, -X * y], [0, 0, 0, x, y, 1, -Y * x, -Y * y]]
    A = np.array(A, float); B = np.array(pb, float).reshape(8)
    return np.linalg.solve(A, B).tolist()

def main():
    truth = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 1100, "height": 900}, device_scale_factor=1)
        for s in SHEETS:
            rng = random.Random(100 + s["id"])
            doc = f"<html><head><meta charset='utf-8'>{font_css()}<style>{CSS}</style></head><body>{sheet_html(s, rng)}</body></html>"
            f = OUT / f"_sheet-{s['id']:02d}.html"; f.write_text(doc, encoding="utf-8")
            pg.goto(f.as_uri()); pg.wait_for_timeout(500)
            pg.evaluate("document.fonts.ready")
            flat = OUT / f"_flat-{s['id']:02d}.png"
            pg.locator(".paper").screenshot(path=str(flat))
            photo = photograph(Image.open(flat).convert("RGB"), s, rng)
            photo.save(OUT / f"sheet-{s['id']:02d}.jpg", quality=78)
            truth.append({"id": s["id"], "file": f"sheet-{s['id']:02d}.jpg", "desc": s["desc"], "event": s["title"],
                          "people": [{k: r[k] for k in ("name", "firm", "email", "phone", "linkedin")} for r in s["rows"] if not r.get("skip") and not r.get("struck")],
                          "should_skip": [r["name"] for r in s["rows"] if r.get("skip") or r.get("struck")]})
        br.close()
    (OUT / "truth.json").write_text(json.dumps(truth, indent=1, ensure_ascii=False), encoding="utf-8")
    print("made", len(truth), "sheets,", sum(len(t["people"]) for t in truth), "people")

if __name__ == "__main__":
    main()
