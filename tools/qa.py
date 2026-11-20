#!/usr/bin/env python3
import json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_m = re.search(r'<link rel="canonical" href="(https?://[^"/]+)/"', open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())
D = _m.group(1) if _m else "https://www.example.com"

pages = [f for f in sorted(os.listdir(ROOT)) if f.endswith(".html")]
VOID = {"meta", "link", "img", "br", "hr", "input", "use", "path", "circle", "rect", "ellipse", "source"}
INLINE_OK = {"p", "li", "a", "button", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "dt", "dd",
             "figcaption", "label", "cite", "summary", "option", "title", "textarea", "strong", "em", "script", "style"}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.h = []          # (level, text, id)
        self.cur_h = None
        self.ids = {}
        self.imgs = []
        self.links = []
        self.bare = []
        self.mains = 0
        self.sections = []
        self.brs = 0
        self.jsonld = []
        self.in_ld = False
        self.ld_buf = ""
        self.meta = {}
        self.link_tags = []
        self.html_attrs = {}
        self.scripts = []
        self.title = ""
        self.in_title = False
        self.faq_text = []
        self.faq_cur = None
        self.skip_first = None
        self.ph = 0
        self.in_ph = False
        self.body_started = False
        self.first_body_a = None

    def handle_starttag(self, t, a):
        d = dict(a)
        if t == "html":
            self.html_attrs = d
        if t == "body":
            self.body_started = True
        if self.body_started and self.first_body_a is None and t == "a":
            self.first_body_a = d
        if "id" in d:
            self.ids[d["id"]] = self.ids.get(d["id"], 0) + 1
        if t == "meta":
            k = d.get("name") or d.get("property")
            if k:
                self.meta[k] = d.get("content", "")
        if t == "link":
            self.link_tags.append(d)
        if t == "title":
            self.in_title = True
        if t == "script":
            if d.get("type") == "application/ld+json":
                self.in_ld = True
                self.ld_buf = ""
            else:
                self.scripts.append(d)
        if t == "main":
            self.mains += 1
            self.main_id = d.get("id")
        if t == "section":
            self.sections.append(d)
        if t == "br":
            self.brs += 1
        if t == "img":
            self.imgs.append(d)
        if t == "a" and "href" in d:
            self.links.append(d["href"])
        if t in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.cur_h = [int(t[1]), "", d.get("id")]
        if "ph" in (d.get("class") or "").split():
            self.in_ph = True
            self.ph += 1
        if t not in VOID:
            self.stack.append((t, d))

    def handle_startendtag(self, t, a):
        self.handle_starttag(t, a)
        if t not in VOID and self.stack and self.stack[-1][0] == t:
            self.stack.pop()

    def handle_endtag(self, t):
        if t == "title":
            self.in_title = False
        if t == "script" and self.in_ld:
            self.in_ld = False
            self.jsonld.append(self.ld_buf)
        if t in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.cur_h:
            self.h.append(tuple(self.cur_h))
            self.cur_h = None
        if t in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == t:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.in_ld:
            self.ld_buf += data
            return
        if self.in_title:
            self.title += data
        if self.cur_h is not None:
            self.cur_h[1] += data
        txt = data.strip()
        if not txt or not self.stack:
            return
        names = [s[0] for s in self.stack]
        if "script" in names or "style" in names or "head" in names:
            return
        parent = names[-1]
        # collect FAQ answers (visible text) for schema comparison
        if "faq-answer" in " ".join((s[1].get("class") or "") for s in self.stack) and parent == "p":
            self.faq_text.append(txt)
        if parent == "div":
            self.bare.append(("div", txt[:50]))
        elif parent == "span" and not any(n in INLINE_OK for n in names[:-1]):
            self.bare.append(("span", txt[:50]))


fails, warns = [], []


def F(page, msg):
    fails.append(f"{page}: {msg}")


def W(page, msg):
    warns.append(f"{page}: {msg}")


sitemap = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
sm_urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
canon_urls = []
ph_total = {}

for pg in pages:
    raw = open(os.path.join(ROOT, pg), encoding="utf-8").read()
    p = P()
    p.feed(raw)
    path = "/" if pg == "index.html" else "/" + pg
    noindex = pg == "404.html"

    # 1 static HTML / no-js
    if "no-js" not in (p.html_attrs.get("class") or ""):
        F(pg, "html lacks class no-js")
    if p.html_attrs.get("lang") != "en":
        F(pg, "html lang missing")
    sc = [s for s in p.scripts]
    if not any(s.get("src") == "/script.js" and "defer" in s for s in sc):
        F(pg, "script.js not deferred")
    if any("src" not in s for s in sc):
        F(pg, "inline script present")

    # 2 headings
    h1 = [h for h in p.h if h[0] == 1]
    if len(h1) != 1:
        F(pg, f"h1 count = {len(h1)}")
    prev = 0
    for lvl, txt, _ in p.h:
        if lvl > prev + 1:
            F(pg, f"heading skip h{prev}->h{lvl}: {txt.strip()[:40]}")
        if not txt.strip():
            F(pg, "empty heading")
        prev = lvl
    if p.h and p.h[0][0] != 1:
        F(pg, "first heading is not h1")

    # 3 semantics
    if p.mains != 1 or p.main_id != "main-content":
        F(pg, f"main count/id wrong ({p.mains}, {p.main_id})")
    for tag in ("<header", "<footer", '<nav class="nav" aria-label="Primary"'):
        if tag not in raw:
            F(pg, f"missing {tag}")
    if not (p.first_body_a and p.first_body_a.get("class") == "skip-link"):
        F(pg, "skip link is not first link in body")
    for s in p.sections:
        if not (s.get("aria-labelledby") or s.get("aria-label")):
            F(pg, f"section without label: {s}")
        lb = s.get("aria-labelledby")
        if lb and lb not in p.ids:
            F(pg, f"aria-labelledby target missing: {lb}")
    dup = [k for k, v in p.ids.items() if v > 1]
    if dup:
        F(pg, f"duplicate ids {dup}")
    if p.brs:
        F(pg, f"<br> used {p.brs}x")
    for kind, txt in p.bare:
        F(pg, f"bare text in <{kind}>: {txt!r}")

    # 4 head
    t = p.title.strip()
    if len(t) > 60:
        F(pg, f"title {len(t)} chars")
    desc = p.meta.get("description", "")
    if not (150 <= len(desc) <= 160) and not noindex:
        F(pg, f"description {len(desc)} chars")
    canon = [l for l in p.link_tags if l.get("rel") == "canonical"]
    if noindex:
        if canon:
            F(pg, "404 should not have canonical")
    else:
        if len(canon) != 1 or canon[0]["href"] != D + path:
            F(pg, f"canonical mismatch {canon}")
        else:
            canon_urls.append(canon[0]["href"])
        if p.meta.get("og:url") != D + path:
            F(pg, "og:url != canonical")
    for k in ("og:title", "og:description", "og:image", "og:type", "og:locale", "twitter:card", "twitter:title",
              "twitter:description", "twitter:image", "dateModified", "viewport"):
        if not p.meta.get(k):
            F(pg, f"missing meta {k}")
    for k in ("og:image", "twitter:image"):
        fn = p.meta.get(k, "").replace(D, "")
        if not os.path.exists(ROOT + fn):
            F(pg, f"{k} file missing {fn}")
    if not any(l.get("rel") == "icon" for l in p.link_tags):
        F(pg, "no favicon link")

    # 5 images
    for im in p.imgs:
        if "alt" not in im:
            F(pg, f"img without alt {im.get('src')}")
        if not (im.get("width") and im.get("height")):
            F(pg, f"img without width/height {im.get('src')}")
        if im.get("src", "").startswith("/") and not os.path.exists(ROOT + im["src"]):
            F(pg, f"img file missing {im['src']}")
        if im.get("alt") == "" and im.get("aria-hidden") != "true":
            F(pg, "decorative img (alt='') without aria-hidden")

    # 6 links
    for href in p.links:
        if href == "#" or href == "":
            F(pg, "dead link href=#")
        elif href.startswith("/"):
            base, _, frag = href.partition("#")
            fn = "index.html" if base in ("", "/") else base.lstrip("/")
            if not os.path.exists(os.path.join(ROOT, fn)):
                F(pg, f"link to missing page {href}")
        elif href.startswith("#"):
            if href[1:] not in p.ids:
                F(pg, f"anchor target missing {href}")
        elif href.startswith("tel:") and href == "tel:":
            F(pg, "empty tel: link")

    # 7 JSON-LD
    if not noindex:
        if not p.jsonld:
            F(pg, "no JSON-LD")
        for blob in p.jsonld:
            try:
                data = json.loads(blob)
            except Exception as e:
                F(pg, f"JSON-LD invalid: {e}")
                continue
            graph = data["@graph"]
            ids = {n.get("@id") for n in graph}
            types = [n["@type"] if isinstance(n["@type"], str) else "/".join(n["@type"]) for n in graph]
            # every @id reference resolves, except WebSite defined only on home
            def refs(o):
                if isinstance(o, dict):
                    if set(o.keys()) == {"@id"}:
                        yield o["@id"]
                    for v in o.values():
                        yield from refs(v)
                elif isinstance(o, list):
                    for v in o:
                        yield from refs(v)
            for r in refs(graph):
                if r not in ids:
                    F(pg, f"JSON-LD unresolved @id {r}")
            faq = [n for n in graph if n["@type"] == "FAQPage"]
            if pg != "about.html" and len(faq) != 1:
                F(pg, "FAQPage missing")
            for f in faq:
                schema_txt = [q["acceptedAnswer"]["text"] for q in f["mainEntity"]]
                if schema_txt != p.faq_text:
                    F(pg, "FAQ schema text != visible text")
                qnames = [q["name"] for q in f["mainEntity"]]
                vis_q = [h[1].strip() for h in p.h if h[0] == 3 and h[1].strip() in qnames]
                if qnames != vis_q:
                    F(pg, "FAQ question text != visible h3 text")
            if pg != "index.html" and "BreadcrumbList" not in types:
                F(pg, "BreadcrumbList missing")
            if pg == "index.html":
                for need in ("Plumber", "WebSite", "WebPage", "ItemList", "FAQPage"):
                    if need not in types:
                        F(pg, f"home graph lacks {need}")
            # no invented data
            blob_l = blob.lower()
            for bad in ("aggregaterating", "\"review\"", "ratingvalue", "[", "example.com/null"):
                if bad in blob_l and bad != "[":
                    F(pg, f"JSON-LD contains {bad}")
            if re.search(r"\[[A-Za-z]", blob):
                F(pg, "placeholder in JSON-LD")

    ph_total[pg] = p.ph
    print(f"{pg:26} h1={len(h1)} headings={len(p.h):2} imgs={len(p.imgs)} links={len(p.links):3} ld_blocks={len(p.jsonld)} placeholders={p.ph}")

# sitemap vs canonical
if sorted(sm_urls) != sorted(canon_urls):
    F("sitemap", f"urls != canonicals\n  sitemap={sorted(sm_urls)}\n  canon  ={sorted(canon_urls)}")
for u in sm_urls:
    if "/404" in u:
        F("sitemap", "404 in sitemap")
robots = open(os.path.join(ROOT, "robots.txt")).read()
if f"Sitemap: {D}/sitemap.xml" not in robots or "Disallow" in robots:
    F("robots.txt", "sitemap line missing or Disallow present")

# css checks
css = open(os.path.join(ROOT, "style.css"), encoding="utf-8").read()
if re.search(r"\.faq[^{]*\{[^}]*display\s*:\s*none", css):
    F("style.css", "FAQ uses display:none")
for need in (".no-js .faq-answer", "grid-template-rows:0fr", ":focus-visible", "prefers-reduced-motion"):
    if need not in css:
        F("style.css", f"missing {need}")

# files
for f in ("robots.txt", "sitemap.xml", ".htaccess", "favicon.svg", "logo.svg", "logo.png", "og-image.png", "404.html", "script.js", "style.css"):
    if not os.path.exists(os.path.join(ROOT, f)):
        F("files", f"missing {f}")
ht = open(os.path.join(ROOT, ".htaccess")).read()
for need in ("mod_deflate", "mod_expires", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "ErrorDocument 404"):
    if need not in ht:
        F(".htaccess", f"missing {need}")

print("\nFAILS:", len(fails))
for x in fails:
    print("  FAIL", x)
print("WARNS:", len(warns))
for x in warns:
    print("  warn", x)
sys.exit(1 if fails else 0)
