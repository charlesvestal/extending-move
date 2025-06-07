import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ——— CONFIG ———
BASE_URL = "https://www.ableton.com/en/live-manual/12/live-instrument-reference/"
ANCHOR   = "drift"
OUT_HTML = "drift.html"
IMG_DIR  = "images"

os.makedirs(IMG_DIR, exist_ok=True)

# ——— FETCH & PARSE ———
resp = requests.get(BASE_URL)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

start = soup.find(id=ANCHOR)
if not start:
    raise RuntimeError(f"Couldn't find #{ANCHOR}")

# collect until next instrument (<h2>)
section_nodes = []
for sib in start.next_siblings:
    if getattr(sib, "name", "") == "h2":
        break
    section_nodes.append(sib)

# build minimal HTML
out = BeautifulSoup(
    "<!doctype html><html><head><meta charset='utf-8'><title>Drift Synth</title></head><body></body></html>",
    "html.parser"
)
body = out.body
h2 = soup.new_tag("h2")
h2.string = start.get_text()
body.append(h2)
for node in section_nodes:
    body.append(node)

# ——— IMAGE EXTRACTION & DOWNLOAD ———
def pick_largest_src(srcset_str):
    candidates = [s.strip() for s in srcset_str.split(",") if s.strip()]
    # each “url width_descriptor”, e.g. "…?w=320 320w"
    max_pair = max(
        ( (int(part.split()[-1].rstrip("w")), part.split()[0]) for part in candidates ),
        key=lambda x: x[0],
        default=(None, None)
    )
    return max_pair[1]  # URL of the largest

for img in body.find_all("img"):
    # prefer data-srcset, else srcset
    srcset_attr = img.get("data-srcset") or img.get("srcset")
    if not srcset_attr:
        # fallback to data-src or src
        url = img.get("data-src") or img.get("src")
    else:
        url = pick_largest_src(srcset_attr)
    if not url:
        continue

    full_url = urljoin(BASE_URL, url)
    fname = os.path.basename(urlparse(full_url).path)
    local_path = os.path.join(IMG_DIR, fname)

    if not os.path.exists(local_path):
        r = requests.get(full_url)
        r.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(r.content)

    # cleanup and rewrite tag
    for attr in ["data-src", "data-srcset", "srcset", "sizes", "class"]:
        if attr in img.attrs:
            del img.attrs[attr]
    img["src"] = os.path.join(os.path.basename(IMG_DIR), fname)

# ——— SAVE RESULT ———
with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(out.prettify(formatter="html"))

print(f"Written {OUT_HTML} + images/") 