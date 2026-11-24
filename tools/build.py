#!/usr/bin/env python3
"""Drain Squad Plumber: static site builder.

Run:  python3 tools/build.py
Edit the CONFIG block below, then re-run. Every page, sitemap.xml, robots.txt
and the JSON-LD are generated from it, so canonical = sitemap = internal links.
"""
import html as H
import json
import os
import re
import shutil

# ───────────────────────── CONFIG: fill these in ─────────────────────────
CONFIG = dict(
    DOMAIN="https://www.example.com",   # SET FIRST: real domain, no trailing slash
    BRAND="Drain Squad Plumber",
    CITY="",                # e.g. "Calgary". Leave empty until known: pages then omit "in <city>"
    GEO_PLACENAME="",       # e.g. "Calgary, Alberta, Canada"  (geo.placename)
    GEO_REGION="",          # e.g. "CA-AB"                      (geo.region)
    LAT="", LNG="",         # e.g. "51.0447", "-114.0719"       (ICBM)
    PHONE_DISPLAY="647-788-2840",       # e.g. "(403) 555-0123"
    PHONE_TEL="+16477882840",           # e.g. "+14035550123"
    EMAIL="info@drainsquadplumbing.ca",   # contact email
    HOURS="",               # e.g. "Mon-Fri 8:00-18:00"
    ADDRESS_TEXT="",        # one-line address shown on the page
    ADDRESS_SCHEMA=None,    # e.g. {"streetAddress":"...","addressLocality":"...","addressRegion":"...","postalCode":"...","addressCountry":"CA"}
    SAME_AS=[],             # list of profile URLs (Google Business Profile, Facebook, ...)
    GOOGLE_REVIEWS_URL="",  # link to the Google reviews page
    MAPS_URL="",            # link to "Get directions"
    LICENSE="",             # licence number, if required where you work
    DATE_PUBLISHED="2026-11-20",
    DATE_MODIFIED="2026-11-20",
    LOCALE="en_US",         # Open Graph locale; change to e.g. en_CA when the country is known
)
# ─────────────────────────────────────────────────────────────────────────

C = CONFIG
D = C["DOMAIN"].rstrip("/")
BRAND = C["BRAND"]
CITY = C["CITY"].strip()
IN = f" in {CITY}" if CITY else ""
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source-single-page.html")
OUT = os.path.dirname(HERE)   # project root (the folder that contains tools/)
LOGO_SVG = os.path.join(HERE, "logo-original.svg")

TELHREF = f"tel:{C['PHONE_TEL']}" if C["PHONE_TEL"] else "#contact"

src = open(SRC, encoding="utf-8").read()


def rep(s, old, new, count=1):
    assert s.count(old) == count, (s.count(old), old[:90])
    return s.replace(old, new)


def esc(t):
    return H.escape(t, quote=False)


def ph(t):
    return re.sub(r"\[([^\]]+)\]", r'<span class="ph">[\1]</span>', esc(t))


# ───────────────────────── extract pieces from the single page ─────────────────────────
css = src[src.index("<style>") + 7: src.index("</style>")].strip()

home_a = src.index('<div class="view" id="view-home">') + len('<div class="view" id="view-home">')
home_b = src.index('<div class="view svc" id="view-drain-cleaning"')
home = src[home_a:home_b].rstrip()
assert home.endswith("</div>")
home = home[:-6].strip()

shared_a = src.index('<section class="contact" id="contact">')
shared_b = src.index("</main>")
shared = src[shared_a:shared_b].strip()          # contact form + location block (on every page)

# ───────────────────────── page data ─────────────────────────
URL = {
    "drain-cleaning": "/drain-cleaning.html",
    "sewer-backup": "/sewer-backup.html",
    "emergency-plumbing": "/emergency-plumbing.html",
    "leak-detection": "/leak-detection.html",
    "about": "/about.html",
}

SERVICES = [  # name, description, page key
    ("Drain cleaning", "Stubborn clogs cleared with professional equipment so water flows again.", "drain-cleaning"),
    ("Clogged drains", "Sinks, tubs, toilets and floor drains, cleared and tested.", "drain-cleaning"),
    ("Sewer line services", "Deep blockages in the main line, handled with the right tools.", "drain-cleaning"),
    ("Sewer backup", "Wastewater coming up? We respond and fix the cause.", "sewer-backup"),
    ("Leaking pipes", "We locate the leak and repair it before it becomes damage.", "leak-detection"),
    ("Plumbing repairs", "Quality workmanship on jobs of every size.", "leak-detection"),
    ("Emergency plumbing", "When it can’t wait, we’re ready to help.", "emergency-plumbing"),
]

ICONS = {
    "tool": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    "drop": '<path d="M12 2.7s7 7.5 7 12a7 7 0 0 1-14 0c0-4.5 7-12 7-12z"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
}
DROP = '<svg class="drop" viewBox="0 0 60 88" aria-hidden="true"><use href="#drop"/></svg>'
BTN = {
    "quote": '<a class="btn btn-primary" href="#contact">Book Free Quote</a>',
    "expert": f'<a class="btn btn-ghost" href="{TELHREF}">Talk to an Expert</a>',
    "expert_p": f'<a class="btn btn-primary" href="{TELHREF}">Talk to an Expert</a>',
}


def pick_desc(cands):
    texts = [c(IN) for c in cands]
    for t in texts:
        if 150 <= len(t) <= 160:
            return t
    return min(texts, key=lambda t: abs(len(t) - 155))


DESC = {
    "home": [
        lambda IN: f"{BRAND} provides professional drain cleaning, clogged drain relief, sewer line services and plumbing repairs{IN}. Honest service and free quotes.",
        lambda IN: f"{BRAND} offers professional drain cleaning, sewer line services and plumbing repairs{IN}. Honest service, clear communication and free quotes.",
        lambda IN: f"{BRAND}: professional drain cleaning, sewer line services and plumbing repairs{IN}. Honest service, clear communication and free quotes.",
    ],
    "drain-cleaning": [
        lambda IN: f"Slow or blocked drain? {BRAND} clears clogs in sinks, tubs, toilets, floor drains and sewer lines{IN} using professional equipment. Free quotes.",
        lambda IN: f"Slow or blocked drain? {BRAND} clears clogs in sinks, tubs, toilets and sewer lines{IN} with professional equipment. Book a free quote today.",
        lambda IN: f"Slow or blocked drain? {BRAND} clears clogs in sinks, tubs, toilets and sewer lines{IN}. Professional equipment, free quotes.",
    ],
    "sewer-backup": [
        lambda IN: f"Sewage or foul smells coming up your drains? {BRAND} clears the blockage{IN}, finds the cause and explains how to prevent a repeat. Free quotes.",
        lambda IN: f"Sewage or bad smells in your drains? {BRAND} clears the blockage{IN}, finds the cause and explains how to prevent a repeat. Free quotes.",
        lambda IN: f"Sewage or bad smells coming up your drains? {BRAND} clears the blockage{IN}, finds the cause and explains how to prevent a repeat.",
    ],
    "emergency-plumbing": [
        lambda IN: f"Burst pipe, sewer backup or no water? Call {BRAND} for urgent plumbing help{IN}. We explain the problem clearly, plus your options and next steps.",
        lambda IN: f"Burst pipe, sewer backup or no water? Call {BRAND} for urgent plumbing help{IN}. We explain what is wrong, your options and the next steps.",
    ],
    "leak-detection": [
        lambda IN: f"Suspect a hidden leak? {BRAND} tracks down the source and repairs it{IN} with as little disruption as possible. Book a free quote or call today.",
        lambda IN: f"Suspect a hidden leak? {BRAND} tracks down the source and repairs it{IN} with as little disruption as possible. Book a free quote today.",
        lambda IN: f"Suspect a hidden leak? {BRAND} tracks down the source of leaks in walls, floors and fixtures{IN} and repairs it carefully. Free quotes.",
    ],
    "about": [
        lambda IN: f"Meet {BRAND}: honest service, clear communication and quality workmanship for drains, sewers and plumbing{IN}. Learn how we work and what we value.",
        lambda IN: f"Meet {BRAND}: honest service, clear communication and quality workmanship for drains and plumbing{IN}. Learn how we work and what we value.",
        lambda IN: f"Meet {BRAND}: honest service, clear communication and quality workmanship for drains, sewers and plumbing{IN}. See how we work.",
    ],
}

PAGES = [
    dict(
        key="drain-cleaning", name="Drain Cleaning",
        titles=[f"Drain Cleaning{IN} | {BRAND}"],
        h1=f"Drain Cleaning{IN}",
        sub="Slow or blocked drain? We clear it with professional equipment and tell you what caused it.",
        buttons=["quote"], icon="tool", color="green",
        list_title="Clogs we clear", list_intro="Most clogs get worse, not better. These are the ones we see most often.",
        items=[
            ("Kitchen sinks that drain slowly or not at all", "Grease, food waste and buildup narrow the pipe over time."),
            ("Showers and tubs that fill while you wash", "Hair and soap scum collect and harden."),
            ("Gurgling toilets or water rising in other fixtures", "Often a sign of a clog further down a shared line."),
            ("Basement floor drains that back up", "This can point to a blocked main line, so don’t wait."),
            ("Main sewer line blockages", "Roots, damaged pipe or long-term buildup can stop the whole system."),
        ],
        over_head="Clear the clog. Restore the flow.",
        over_text="A slow drain is easy to ignore until it backs up. Drain Squad Plumber finds what is blocking the line and removes it, using professional equipment and proven techniques. We explain what we found and what to do so it doesn’t come back.",
        why=[("Honest service", "You hear what is wrong and what it takes to fix it."),
             ("Clear communication", "You know what we’re doing and why before we start."),
             ("Done right the first time", "Quality workmanship so the drain stays clear.")],
        faq_title="Drain cleaning: frequently asked questions", faq_intro="Quick answers about drain cleaning.",
        faq=[
            ("How do I know if I need professional drain cleaning?", "If water drains slowly, backs up into other fixtures or the clog keeps returning, it’s time to call. Plunging can help briefly, but a repeat clog usually means the blockage is deeper."),
            ("Are chemical drain cleaners safe?", "They can damage pipes, especially older ones, and often fail on deeper clogs. Mechanical clearing is usually the safer choice."),
            ("How long does it take to clear a clog?", "It depends on where the clog is and how severe it is. We’ll give you an idea of the time once we see the problem."),
            ("Can you tell what caused the clog?", "We look for the cause as we work and explain it, whether it’s grease, hair, debris or something deeper in the line."),
            ("What if the clog is in the main sewer line?", "We handle main line blockages too. Tell us what you are seeing and we’ll advise on the next step."),
        ],
    ),
    dict(
        key="sewer-backup", name="Sewer Backup",
        titles=[f"Sewer Backup Help{IN} | {BRAND}"],
        h1=f"Sewer Backup Help{IN}",
        sub="Sewage or bad smells coming up your drains? We clear the blockage and explain how to prevent a repeat.",
        buttons=["expert_p", "quote"], icon="drop", color="blue",
        list_title="What causes sewer backups", list_intro="Knowing the cause is how you stop the next one.",
        items=[
            ("Roots in the main line", "They enter old pipes and grow until little can pass."),
            ("Wipes, grease and debris", "What goes down the drain doesn’t always go away."),
            ("Pipes that sag, crack or collapse", "A damaged section can stop the whole line."),
            ("Heavy rain", "Overloaded municipal sewers can push water back toward your home."),
            ("Earlier clogs that were never fully cleared", "A partial fix means the next backup is only a matter of time."),
        ],
        over_head="When the drain backs up, everything stops.",
        over_text="A sewer backup is a health and property risk, so treat it as urgent. Whether the cause is roots, grease, damaged pipe or a surge in the municipal sewer, Drain Squad Plumber clears the line and works to find the real cause so the fix lasts.",
        why=[("Clear next steps", "We explain what is happening and what to do next."),
             ("Quality workmanship", "Proven techniques and professional equipment."),
             ("Real fixes, not quick patches", "We look for the cause, not just the symptom.")],
        faq_title="Sewer backup: frequently asked questions", faq_intro="Quick answers about sewer backups.",
        faq=[
            ("What should I do first during a sewer backup?", "Stop using water: no flushing, laundry or running taps. If it is safe, shut off your home’s main water valve. Then call us."),
            ("Why did this happen?", "Common causes are roots, grease buildup, damaged pipe and overloaded municipal sewers. We look for the cause so the repair lasts."),
            ("Can heavy rain cause a sewer backup?", "Yes. When municipal sewers are overwhelmed, water can be pushed back toward homes. Ask us how to reduce the risk at your property."),
            ("Will insurance cover a sewer backup?", "Coverage depends on your policy and often requires specific sewer backup coverage. Photograph the damage and keep records of the work done."),
            ("How can I prevent it in the future?", "Keep wipes and grease out of the drains, and book drain cleaning at the first sign of a slowdown. Ask us what suits your home."),
        ],
    ),
    dict(
        key="emergency-plumbing", name="Emergency Plumbing",
        titles=[f"Emergency Plumbing{IN} | {BRAND}"],
        h1=f"Emergency Plumbing{IN}",
        sub="Burst pipe, backed-up drain or no water? Call us and we’ll help you stop the damage.",
        buttons=["expert_p", "quote"], icon="phone", color="green",
        list_title="Emergencies we handle", list_intro="If water is damaging your home or making daily life impossible, don’t wait.",
        items=[
            ("Burst or leaking pipes", "We locate the leak and work to stop further damage."),
            ("Sewer line backups", "Wastewater coming up instead of going down."),
            ("No running water", "We find the source and get water flowing again."),
            ("Major clogs and slow drains", "Blockages cleared with professional equipment."),
            ("Water in your home", "We help stop the source and advise on the next steps."),
            ("Overflowing toilets", "We find the cause and restore control."),
        ],
        over_head="Plumbing problems don’t wait. Neither should you.",
        over_text="A burst pipe or a sewer backup rarely arrives at a convenient time. Drain Squad Plumber helps with urgent leaks, backups and blockages, explains clearly what is wrong, and tells you what comes next.",
        why=[("Help when you need it", "From routine maintenance to emergency calls."),
             ("Clear communication", "We explain the problem and your options."),
             ("Quality workmanship", "Repairs done right the first time.")],
        faq_title="Emergency plumbing: frequently asked questions", faq_intro="Quick answers about urgent plumbing.",
        faq=[
            ("What counts as a plumbing emergency?", "Flooding, a sewage backup, no running water, or a pipe that won’t stop leaking. If water is damaging your home or creating a health risk, call us."),
            ("Can I shut off the water myself?", "Yes, if it is safe. Close your home’s main water shutoff valve, usually where the supply line enters the house. If you can’t find it, call us."),
            ("Will you fix it right away or only stop the damage?", "Where possible we repair the problem on the spot. If not, we protect your home and explain the plan for the next step."),
        ],
    ),
    dict(
        key="leak-detection", name="Leak Detection & Repair",
        titles=[f"Leak Detection & Repair{IN} | {BRAND}"],
        h1=f"Leak Detection & Repair{IN}",
        sub="Hidden leak? Find it before it causes costly damage.",
        buttons=["quote"], icon="search", color="blue",
        list_title="Signs you may have a leak", list_intro="Hidden leaks rarely stay hidden for long if you know what to look for.",
        items=[
            ("A sudden jump in your water bill", "Same habits, higher cost."),
            ("Soft or warped spots in walls, ceilings or floors", "Water is probably sitting underneath."),
            ("Musty or mildew smells", "Moisture is building up where it shouldn’t."),
            ("The sound of running water when nothing is on", "A classic clue."),
            ("Low pressure, or hot water that runs out fast", "Leaks can reduce both."),
            ("Water stains or bubbling paint", "Moisture inside the wall often shows on the surface."),
        ],
        over_head="Find the leak before it finds you.",
        over_text="Leaks hide inside walls, under floors and behind fixtures, quietly raising your water bill and damaging your home. Drain Squad Plumber tracks down the source, explains what is happening and repairs it with as little disruption as possible.",
        why=[("Experienced team", "Answers based on evidence, not guesswork."),
             ("Professional equipment", "The right tools for the job."),
             ("Careful work", "We aim to keep disruption and damage to a minimum.")],
        faq_title="Leak detection: frequently asked questions", faq_intro="Quick answers about hidden leaks.",
        faq=[
            ("How can I tell if I have a hidden leak?", "Turn off every tap and appliance, then check your water meter. If it keeps moving, water is escaping somewhere. Also watch for musty smells, warped surfaces and damp spots."),
            ("How do plumbers find hidden leaks?", "We start with where the water shows up and the most likely sources, then narrow it down. Sometimes we need access behind a wall or ceiling to confirm the source."),
            ("Is leak detection expensive?", "It costs far less than water damage. We recommend detection only when it makes sense for your situation, and we explain the price first."),
            ("Can I find a leak myself?", "You can check visible pipes, fixtures and appliances. For a hidden leak, professional help saves guesswork and unnecessary damage."),
            ("Can leak sensors help?", "Smart leak sensors and automatic shut-off valves can warn you early, even when you are away. Ask us if prevention is your goal."),
        ],
    ),
]

HOME_FAQ = [
    ("What services does Drain Squad Plumber offer?", "We specialize in drain cleaning, clogged drains, sewer line services and plumbing repairs, including leaking pipes, sewer backups and emergency plumbing. If you’re not sure what you need, tell us what’s going on and we’ll help you work it out."),
    ("How much do your services cost?", "Every job is different, so the prices on this page are estimated ranges. We explain your options and the price before we start. You can request a free estimate online or by phone."),
    ("Do you offer payment plans?", "Ask us about monthly payment options that let you spread the cost over time. See “How payment plans work” above for the steps."),
    ("What should I do if I have a sewer backup or a plumbing emergency?", "Call us right away. Our team can help with emergency plumbing and sewer backups, and we’ll explain the next steps and what to expect."),
    ("Which areas do you serve?",
     (f"We serve {CITY} and the surrounding area. " if CITY else "") + "Check the list of areas above, and if you don’t see yours, get in touch and we’ll let you know if we can help."),
]
HOME_FAQ_TITLE = "Frequently asked questions about drain and plumbing services"

ABOUT_CODE = [
    ("Honest service", "We tell you what is wrong and what it takes to fix it."),
    ("Clear communication", "You are kept informed from the first call to the finished job."),
    ("Quality workmanship", "Proven techniques, done right the first time."),
    ("Professional equipment", "The right tools to find the real cause."),
    ("Help when you need it", "From routine drain maintenance to emergency calls."),
]
ABOUT_DIFF = [
    ("We find the real problem", "We look for the cause so the fix lasts."),
    ("We take pride in the job", "No shortcuts and no “good enough”."),
    ("You know what to expect", "We explain the work and your options before we start."),
]

HOME_DESC = pick_desc(DESC["home"])
ABOUT_DESC = pick_desc(DESC["about"])


# ───────────────────────── helpers ─────────────────────────
def pick_title(cands):
    for t in cands:
        if len(t) <= 60:
            return t
    return cands[-1][:60]


def rows(items):
    lis = "".join(f"<li>{DROP}<div><strong>{ph(t)}</strong><span>{ph(d)}</span></div></li>" for t, d in items)
    return f'<ul class="rows two">{lis}</ul>'


def why_block(items):
    return '<div class="svc-why">' + "".join(f"<div><h3>{ph(t)}</h3><p>{ph(d)}</p></div>" for t, d in items) + "</div>"


def faq_section(title, intro, qa):
    items = []
    for i, (q, a) in enumerate(qa, 1):
        items.append(
            f'<div class="faq-item">'
            f'<h3><button class="faq-trigger" type="button" id="faq-q{i}" aria-expanded="true" aria-controls="faq-a{i}">{esc(q)}</button></h3>'
            f'<div class="faq-answer" id="faq-a{i}" role="region" aria-labelledby="faq-q{i}"><div class="inner"><p>{esc(a)}</p></div></div>'
            f'</div>')
    return (f'<section class="section faq" id="faq">\n    <div class="wrap">\n      <div class="sec-head">\n'
            f'        <h2 class="display">{esc(title)}</h2>\n        <p>{esc(intro)}</p>\n      </div>\n'
            f'      <div class="faq-list">\n        ' + "\n        ".join(items) + '\n      </div>\n    </div>\n  </section>')


def label_sections(h):
    """Give every <section> without aria-label an aria-labelledby that points at its first h1/h2."""
    edits, used = [], set(re.findall(r'\bid="([^"]+)"', h))
    for m in re.finditer(r"<section\b([^>]*)>", h):
        attrs = m.group(1)
        if "aria-label" in attrs:
            continue
        nxt = h.find("<section", m.end())
        window = h[m.end(): nxt if nxt != -1 else len(h)]
        hm = re.search(r"<(h[12])\b([^>]*)>(.*?)</\1>", window, flags=re.S)
        if not hm:
            continue
        hid = re.search(r'\bid="([^"]+)"', hm.group(2))
        if hid:
            label_id, needs_id = hid.group(1), False
        else:
            sid = re.search(r'\bid="([^"]+)"', attrs)
            cls = re.search(r'\bclass="([^"]+)"', attrs)
            if sid:
                base = sid.group(1)
            else:
                words = re.sub(r"<[^>]+>", "", hm.group(3))
                words = re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-").split("-")[:4]
                base = "-".join(words) or (cls.group(1).split()[0] if cls else "section")
            label_id, n = f"{base}-h", 2
            while label_id in used:
                label_id, n = f"{base}-{n}-h", n + 1
            used.add(label_id)
            needs_id = True
        edits.append((m, hm, m.end(), needs_id, label_id))
    for m, hm, off, needs_id, label_id in reversed(edits):
        if needs_id:
            a = off + hm.start()
            end_open = off + hm.start() + len(f"<{hm.group(1)}{hm.group(2)}>")
            tag = h[a:end_open]
            h = h[:a] + tag[:-1] + f' id="{label_id}">' + h[end_open:]
        s1 = m.end()
        h = h[:s1 - 1] + f' aria-labelledby="{label_id}">' + h[s1:]
    return h


def fill(h):
    """Substitute known config values for the visible placeholders."""
    if C["PHONE_DISPLAY"]:
        tel_link = f'<a href="{TELHREF}">{esc(C["PHONE_DISPLAY"])}</a>'
        h = h.replace('<a href="#contact"><span class="ph">[Phone]</span></a>', tel_link)
        h = h.replace('<p>Call <span class="ph">[Phone]</span></p>', f'<p>Call {tel_link}</p>')
        h = h.replace('<span class="ph">[Phone]</span>', esc(C["PHONE_DISPLAY"]))
    h = h.replace('href="tel:"', f'href="{TELHREF}"')
    if C["EMAIL"]:
        mail = f'<a href="mailto:{C["EMAIL"]}">{esc(C["EMAIL"])}</a>'
        h = h.replace('<p class="contact-hours">', f'<p class="contact-email">Email: {mail}</p>\n        <p class="contact-hours">', 1)
        h = h.replace('<div><dt>Hours</dt>', f'<div><dt>Email</dt><dd>{mail}</dd></div>\n        <div><dt>Hours</dt>', 1)
    if C["HOURS"]:
        h = h.replace('<span class="ph">[Hours]</span>', esc(C["HOURS"]))
    if C["ADDRESS_TEXT"]:
        h = h.replace('<span class="ph">[Street address, City, Province/State, Postal code]</span>', esc(C["ADDRESS_TEXT"]))
    if C["LICENSE"]:
        h = h.replace('<span class="ph">[Number]</span>', esc(C["LICENSE"]))
    if CITY:
        h = h.replace('<span class="ph">[City]</span>', esc(CITY))
    return h


# ───────────────────────── shared chrome ─────────────────────────
NAV = [("Services", "/#services"), ("Pricing", "/#pricing"), ("Why us", "/#why"),
       ("Reviews", "/#reviews"), ("Areas", "/#areas"), ("About", URL["about"])]

DEFS = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
        '<symbol id="drop" viewBox="0 0 60 88"><path d="M30 0C30 0 0 36 0 58a30 30 0 0 0 60 0C60 36 30 0 30 0Z"/></symbol>'
        "</defs></svg>")

HEADER = f'''<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/" aria-label="{BRAND}, home">
      <img class="logo-art" src="logo.svg" width="1380" height="900" alt="" aria-hidden="true">
    </a>
    <nav class="nav" id="primary-nav" aria-label="Primary">
      {"".join(f'<a href="{u}">{n}</a>' for n, u in NAV)}
    </nav>
    <div class="header-actions">
      {BTN["expert"]}
      {BTN["quote"]}
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav" aria-label="Open menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>'''


def footer():
    contact = []
    contact.append(f'<p>Call <span class="ph">[Phone]</span></p>')
    if C["EMAIL"]:
        contact.append(f'<p>Email: <a href="mailto:{C["EMAIL"]}">{esc(C["EMAIL"])}</a></p>')
    contact.append(f'<p>Hours: <span class="ph">[Hours]</span></p>')
    contact.append(f'<p><span class="ph">[Street address, City, Province/State, Postal code]</span></p>')
    lic = '<p>License #: <span class="ph">[Number]</span></p>'
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <a class="brand" href="/" aria-label="{BRAND}, back to home">
          <img class="logo-art" src="logo.svg" width="1380" height="900" alt="" aria-hidden="true" loading="lazy">
        </a>
        <p class="footer-tagline">Your Drain Problems, Our Mission.</p>
      </div>
      <div class="footer-contact">
        <h2>Contact</h2>
        {"".join(contact)}
      </div>
      <div>
        <h2>Drains &amp; Sewers</h2>
        <ul>
          <li><a href="{URL['drain-cleaning']}">Drain cleaning</a></li>
          <li><a href="{URL['drain-cleaning']}">Clogged drains</a></li>
          <li><a href="{URL['drain-cleaning']}">Sewer line services</a></li>
          <li><a href="{URL['sewer-backup']}">Sewer backup</a></li>
        </ul>
      </div>
      <div>
        <h2>Plumbing</h2>
        <ul>
          <li><a href="{URL['leak-detection']}">Leaking pipes</a></li>
          <li><a href="{URL['leak-detection']}">Plumbing repairs</a></li>
          <li><a href="{URL['emergency-plumbing']}">Emergency plumbing</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      {lic}
      <p>© 2026 {BRAND}. All rights reserved.</p>
      <nav aria-label="Footer">
        <a href="{URL['about']}">About us</a>
      </nav>
    </div>
  </div>
</footer>'''


def breadcrumb(name):
    return (f'<nav class="breadcrumb" aria-label="Breadcrumb"><div class="wrap"><ol>'
            f'<li><a href="/">Home</a></li><li><span aria-current="page">{esc(name)}</span></li></ol></div></nav>')


# ───────────────────────── schema.org ─────────────────────────
ORG_ID = f"{D}/#organization"
SITE_ID = f"{D}/#website"


def org_node():
    n = {
        "@type": "Plumber",
        "@id": ORG_ID,
        "name": BRAND,
        "url": f"{D}/",
        "logo": {"@type": "ImageObject", "url": f"{D}/logo.png", "width": 600, "height": 391},
        "image": f"{D}/og-image.png",
        "description": "Professional drain cleaning, clogged drain, sewer line and plumbing repair services.",
        "slogan": "Your Drain Problems, Our Mission.",
        "knowsAbout": ["Drain cleaning", "Clogged drains", "Sewer line services", "Sewer backup",
                       "Leak detection and repair", "Plumbing repairs", "Emergency plumbing"],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Drain and plumbing services",
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": nm}} for nm, _, _ in SERVICES],
        },
    }
    if C["PHONE_TEL"]:
        n["telephone"] = C["PHONE_TEL"]
    if C["EMAIL"]:
        n["email"] = C["EMAIL"]
    if C["ADDRESS_SCHEMA"]:
        n["address"] = dict({"@type": "PostalAddress"}, **C["ADDRESS_SCHEMA"])
    if CITY:
        n["areaServed"] = {"@type": "City", "name": CITY}
    if C["LAT"] and C["LNG"]:
        n["geo"] = {"@type": "GeoCoordinates", "latitude": C["LAT"], "longitude": C["LNG"]}
    if C["SAME_AS"]:
        n["sameAs"] = C["SAME_AS"]
    return n


def faq_node(url, qa):
    return {
        "@type": "FAQPage", "@id": f"{url}#faq",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa],
    }


def crumbs_node(url, name):
    return {
        "@type": "BreadcrumbList", "@id": f"{url}#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{D}/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": url},
        ],
    }


def webpage_node(url, title, desc, types=("WebPage",), extra=None):
    n = {
        "@type": list(types) if len(types) > 1 else types[0],
        "@id": f"{url}#webpage", "url": url, "name": title, "description": desc,
        "inLanguage": "en", "datePublished": C["DATE_PUBLISHED"], "dateModified": C["DATE_MODIFIED"],
        "publisher": {"@id": ORG_ID}, "about": {"@id": ORG_ID},
        "primaryImageOfPage": {"@type": "ImageObject", "url": f"{D}/og-image.png"},
    }
    if extra:
        n.update(extra)
    return n


def graph(nodes):
    return {"@context": "https://schema.org", "@graph": nodes}


# ───────────────────────── <head> ─────────────────────────
def head(path, title, desc, graph_obj=None, noindex=False):
    url = f"{D}{path}"
    t, dsc = esc(title), H.escape(desc, quote=True)
    geo = ""
    if C["GEO_PLACENAME"]:
        geo += f'<meta name="geo.placename" content="{H.escape(C["GEO_PLACENAME"], quote=True)}">\n'
    if C["GEO_REGION"]:
        geo += f'<meta name="geo.region" content="{H.escape(C["GEO_REGION"], quote=True)}">\n'
    if C["LAT"] and C["LNG"]:
        geo += f'<meta name="ICBM" content="{C["LAT"]}, {C["LNG"]}">\n'
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large"
    ld = ""
    if graph_obj:
        ld = '<script type="application/ld+json">\n' + json.dumps(graph_obj, ensure_ascii=False, indent=2) + "\n</script>\n"
    canon = "" if noindex else f'<link rel="canonical" href="{url}">\n'
    return f'''<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{dsc}">
<meta name="robots" content="{robots}">
{canon}{geo}<meta name="dateModified" content="{C["DATE_MODIFIED"]}">
<meta name="theme-color" content="#0B2A5B">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="{C["LOCALE"]}">
<meta property="og:title" content="{H.escape(title, quote=True)}">
<meta property="og:description" content="{dsc}">
<meta property="og:image" content="{D}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{BRAND} logo">
<meta property="og:url" content="{url}">
<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{H.escape(title, quote=True)}">
<meta name="twitter:description" content="{dsc}">
<meta name="twitter:image" content="{D}/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=Barlow:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
{ld}</head>'''


MOBILE_BAR = f'''<div class="mobile-bar">
  <a class="btn btn-ghost" href="{TELHREF}">Call us</a>
  <a class="btn btn-primary" href="#contact">Free Quote</a>
</div>'''


def document(path, title, desc, main_html, graph_obj=None, crumb_name=None, noindex=False):
    main_html = label_sections(main_html)
    header = HEADER.replace('href="#contact"', 'href="/#contact"') if noindex else HEADER
    mobile_bar = MOBILE_BAR.replace('href="#contact"', 'href="/#contact"') if noindex else MOBILE_BAR
    body = f'''<body>
<a class="skip-link" href="#main-content">Skip to main content</a>
{DEFS}
{header}
{breadcrumb(crumb_name) if crumb_name else ""}
<main id="main-content">

{main_html}

</main>

{footer()}
{mobile_bar}

<script src="script.js" defer></script>
</body>'''
    doc = f'<!DOCTYPE html>\n<html lang="en" class="no-js">\n{head(path, title, desc, graph_obj, noindex)}\n{body}\n</html>\n'
    return localize_links(fill(doc))


def localize_links(doc):
    """Make internal hrefs relative so navigation works both locally and on a server."""
    doc = doc.replace('href="/#', 'href="index.html#')
    doc = doc.replace('href="/"', 'href="index.html"')
    return re.sub(r'href="/([\w-]+\.html)', r'href="\1', doc)


# ───────────────────────── shared sections (contact + location) ─────────────────────────
def shared_sections():
    s = shared
    s = s.replace('<span class="ph">[Offer terms', '<span class="ph">[Offer terms')  # no-op, keeps intent explicit
    if not C["MAPS_URL"]:
        s = rep(s, '<a class="locate-link" href="#">Get directions to Drain Squad Plumber</a>\n      ', "")
    else:
        s = rep(s, 'href="#">Get directions', f'href="{C["MAPS_URL"]}" target="_blank" rel="noopener">Get directions')
    if CITY:
        s = rep(s, 'Find Drain Squad Plumber in <span class="ph">[City]</span>', f"Find Drain Squad Plumber in {esc(CITY)}")
        s = rep(s, 'Serving <span class="ph">[City]</span> and the surrounding area. Call us', f"Serving {esc(CITY)} and the surrounding area. Call us")
    else:
        s = rep(s, 'Find Drain Squad Plumber in <span class="ph">[City]</span>', "Find Drain Squad Plumber")
        s = rep(s, 'Serving <span class="ph">[City]</span> and the surrounding area. Call us', "Serving the surrounding area. Call us")
    return s


# ───────────────────────── pages ─────────────────────────
def build_home():
    h = home
    # city-dependent copy
    if CITY:
        h = rep(h, 'services in <span class="ph">[City &amp; surrounding areas]</span>:', f"services in {esc(CITY)} and the surrounding area:")
        h = rep(h, 'Serving <span class="ph">[City]</span> and the surrounding area.</h2>', f"Serving {esc(CITY)} and the surrounding area.</h2>")
    else:
        h = rep(h, 'services in <span class="ph">[City &amp; surrounding areas]</span>:', "services:")
        h = rep(h, 'Serving <span class="ph">[City]</span> and the surrounding area.</h2>', "Areas we serve.</h2>")
    # strip CTA
    if C["PHONE_DISPLAY"]:
        pass
    else:
        h = rep(h, '<a class="btn btn-primary" href="tel:">Call <span class="ph">[Phone]</span></a>',
                '<a class="btn btn-primary" href="#contact">Talk to an Expert</a>')
    # drafting notes that are not content
    h = rep(h, ' <span class="ph">[Confirm plans, provider and terms before publishing.]</span>', "")
    h = rep(h, '<p class="how-note"><span class="ph">[Optional: credit-check or pre-qualification note. Add only if your financing provider confirms it.]</span></p>\n          ', "")
    # reviews: no dead "#" links
    h = re.sub(r'\s*<div class="gsum-actions">.*?</div>', "", h, count=1, flags=re.S)
    if C["GOOGLE_REVIEWS_URL"]:
        link = (f'<div class="gsum-actions"><a class="btn btn-ghost" href="{C["GOOGLE_REVIEWS_URL"]}" target="_blank" rel="noopener">Read all reviews</a></div>')
        h = rep(h, '</div>\n      <div class="reviews-grid">', f'{link}\n      </div>\n      <div class="reviews-grid">')
    # text in <p>, not <span>/<div>
    h = rep(h, '<span class="gsum-num display"><span class="ph">[4.9]</span></span>', '<p class="gsum-num display"><span class="ph">[4.9]</span></p>')
    h = re.sub(r'<div class="stars" (role="img" aria-label="[^"]*")>(★+)</div>', r'<p class="stars" \1>\2</p>', h)
    h = h.replace('<div><cite><span class="ph">[Name]</span></cite><span class="rev-date"><span class="ph">[Date]</span></span></div>',
                  '<div><p class="rev-name"><cite><span class="ph">[Name]</span></cite></p><p class="rev-date"><span class="ph">[Date]</span></p></div>')
    h = rep(h, '<span class="promo-amount display">$25 Off</span>', '<p class="promo-amount display">$25 Off</p>')
    h = rep(h, '<span class="promo-what">any plumbing</span>', '<p class="promo-what">any plumbing</p>')
    h = rep(h, '<span class="promo-cta">Press here to get an offer</span>', '<p class="promo-cta">Press here to get an offer</p>')
    h = rep(h, '<span class="promo-terms"><span class="ph">[Offer terms, e.g. first-time customers only]</span></span>',
            '<p class="promo-terms"><span class="ph">[Offer terms, e.g. first-time customers only]</span></p>')
    h = h.replace(' style="margin:0"', "")
    # hero logo: img with width/height, not inline svg
    h = re.sub(r'<svg class="logo-art" viewBox="0 0 1400 1020" role="img" aria-label="([^"]*)">.*?</svg>',
               r'<img class="logo-art" src="logo.svg" width="1380" height="900" alt="\1" fetchpriority="high">', h, count=1, flags=re.S)
    # links to real pages
    for key, u in URL.items():
        h = h.replace(f'href="#{key}"', f'href="{u}"')
    # FAQ: button accordion, h3 questions, schema-identical text
    a = h.index('<section class="section faq" id="faq">')
    b = h.index("</section>", a) + len("</section>")
    h = h[:a] + faq_section(HOME_FAQ_TITLE, "Quick answers about our drain and plumbing services.", HOME_FAQ) + h[b:]
    return h + "\n\n  " + shared_sections()


def service_main(v):
    url = f"{D}{URL[v['key']]}"
    hero = f'''<section class="svc-hero">
    <div class="wrap">
      <div>
        <h1 class="display">{esc(v["h1"])}</h1>
        <p class="svc-sub">{esc(v["sub"])}</p>
        <div class="hero-actions">{" ".join(BTN[b] for b in v["buttons"])}</div>
      </div>
      <div class="svc-art mp-{v["color"]}" aria-hidden="true"><svg viewBox="0 0 24 24">{ICONS[v["icon"]]}</svg></div>
    </div>
  </section>'''
    body = f'''{hero}
  <section class="section svc-list">
    <div class="wrap">
      <div class="sec-head">
        <h2 class="display">{esc(v["list_title"])}</h2>
        <p>{esc(v["list_intro"])}</p>
      </div>
      {rows(v["items"])}
    </div>
  </section>
  <section class="svc-over">
    <div class="wrap">
      <h2 class="display">{esc(v["over_head"])}</h2>
      <p class="lead">{esc(v["over_text"])}</p>
      {why_block(v["why"])}
    </div>
  </section>
  {faq_section(v["faq_title"], v["faq_intro"], v["faq"])}

  {shared_sections()}'''
    return body


def service_graph(v, title, desc):
    url = f"{D}{URL[v['key']]}"
    svc = {"@type": "Service", "@id": f"{url}#service", "name": v["name"], "serviceType": v["name"],
           "description": v["sub"], "url": url, "provider": {"@id": ORG_ID}}
    if CITY:
        svc["areaServed"] = {"@type": "City", "name": CITY}
    wp = webpage_node(url, title, desc, extra={"breadcrumb": {"@id": f"{url}#breadcrumb"}, "mainEntity": {"@id": f"{url}#service"}})
    return graph([org_node(), wp, svc, crumbs_node(url, v["name"]), faq_node(url, v["faq"])])


def about_main():
    return f'''<section class="svc-hero">
    <div class="wrap">
      <div>
        <h1 class="display">About {BRAND}</h1>
        <p class="svc-sub">Professional drain and plumbing service built on honest work and clear communication.</p>
        <div class="hero-actions">{BTN["expert_p"]}</div>
      </div>
      <div class="svc-art mp-green" aria-hidden="true"><svg viewBox="0 0 24 24">{ICONS["shield"]}</svg></div>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <div class="sec-head" style="margin-bottom:0">
        <h2 class="display">Our mission</h2>
        <p>Our mission is simple: solve plumbing problems quickly and efficiently, with quality workmanship you can trust.</p>
      </div>
    </div>
  </section>
  <section class="section svc-list" style="padding-top:0">
    <div class="wrap">
      <div class="sec-head">
        <h2 class="display">Our code</h2>
      </div>
      {rows(ABOUT_CODE)}
    </div>
  </section>
  <section class="svc-over">
    <div class="wrap">
      <h2 class="display">The Drain Squad difference</h2>
      {why_block(ABOUT_DIFF)}
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <div class="sec-head" style="margin-bottom:0">
        <h2 class="display">Meet the team</h2>
        <p>The people who show up at your door.</p>
        <p style="margin-top:20px"><a class="btn btn-primary" href="/#team">Meet the team</a></p>
      </div>
    </div>
  </section>

  {shared_sections()}'''


def build_404():
    return f'''<section class="section not-found">
    <div class="wrap">
      <h1 class="display">Page not found</h1>
      <p class="svc-sub" style="margin-inline:auto">The page you are looking for doesn’t exist or has moved. Try one of these instead.</p>
      <div class="hero-actions" style="justify-content:center">
        <a class="btn btn-primary" href="/">Go to the home page</a>
        <a class="btn btn-ghost" href="{URL["drain-cleaning"]}">Drain cleaning</a>
        <a class="btn btn-ghost" href="{URL["emergency-plumbing"]}">Emergency plumbing</a>
      </div>
    </div>
  </section>'''


# ───────────────────────── write everything ─────────────────────────
os.makedirs(OUT, exist_ok=True)

written = {}   # path -> (title, desc)


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)


# CSS
css = css.replace(".site-footer h3{", ".site-footer h2{").replace(".svc-why strong{", ".svc-why h3{").replace("aspect-ratio:1400/1020", "aspect-ratio:1380/900")
css = "\n".join(l for l in css.split("\n")
                if not (l.startswith(".faq-item summary") or l.startswith(".faq-item[open]") or l.startswith(".faq-a{")))
css += """

/* ===== SEO build additions ===== */
.skip-link{position:absolute;left:12px;top:-80px;z-index:100;padding:10px 16px;background:#0B2A5B;color:#fff;font-weight:700;border-radius:6px;text-decoration:none}
.skip-link:focus{top:calc(env(safe-area-inset-top,0px) + 12px)}
.breadcrumb{background:var(--bg-alt)}
.breadcrumb ol{display:flex;flex-wrap:wrap;gap:6px 10px;margin:0;padding:16px 0 0;font-size:.95rem;list-style:none}
.breadcrumb li+li::before{content:"/";margin-right:10px;color:var(--ink-soft)}
.breadcrumb a{text-decoration:underline;text-decoration-color:var(--green);text-underline-offset:4px}
.breadcrumb+main .svc-hero{padding-top:28px}
.footer-bottom p{margin:0}
.not-found{text-align:center}
/* spans that became <p> keep their old look */
.gsum-score .gsum-num{margin:0;font-weight:800}
.review .rev-name{font-size:1rem}
.review .rev-date{font-size:.9rem}
.review .stars{font-size:1.35rem}

/* FAQ accordion: answers always stay in the DOM; without JS they are open */
.faq-item h3{margin:0;font-size:inherit;line-height:inherit}
.faq-trigger{display:flex;align-items:center;justify-content:space-between;gap:20px;width:100%;padding:22px 0;background:none;border:0;color:inherit;font-family:var(--display);font-weight:800;font-size:1.7rem;line-height:1.1;text-align:left;cursor:pointer}
.faq-trigger::after{content:"";flex:none;width:12px;height:12px;margin-top:-6px;border-right:3px solid var(--ink);border-bottom:3px solid var(--ink);transform:rotate(45deg);transition:transform .2s ease}
.faq-trigger[aria-expanded="true"]::after{margin-top:6px;transform:rotate(-135deg)}
.faq-answer{display:grid;grid-template-rows:0fr;transition:grid-template-rows .25s ease}
.faq-answer .inner{min-height:0;overflow:hidden;visibility:hidden;transition:visibility 0s .25s}
.faq-answer p{max-width:38em;padding:0 40px 24px 0;color:var(--ink-soft)}
.faq-item.is-open .faq-answer{grid-template-rows:1fr}
.faq-item.is-open .faq-answer .inner{visibility:visible;transition-delay:0s}
.no-js .faq-answer{grid-template-rows:1fr}
.no-js .faq-answer .inner{visibility:visible}
@media (prefers-reduced-motion:reduce){.faq-answer,.faq-answer .inner,.faq-trigger::after{transition:none}}

/* ───────── mobile menu + sticky call bar ───────── */
.nav-toggle{display:none;width:46px;height:46px;padding:0;border:2px solid var(--ink);border-radius:8px;background:transparent;cursor:pointer;flex-direction:column;align-items:center;justify-content:center;gap:5px}
.nav-toggle span{display:block;width:22px;height:3px;background:var(--ink);border-radius:2px;transition:transform .25s ease,opacity .2s ease}
.nav-toggle[aria-expanded="true"] span:nth-child(1){transform:translateY(8px) rotate(45deg)}
.nav-toggle[aria-expanded="true"] span:nth-child(2){opacity:0}
.nav-toggle[aria-expanded="true"] span:nth-child(3){transform:translateY(-8px) rotate(-45deg)}
.mobile-bar{display:none}
@media (max-width:980px){
  .js .nav-toggle{display:flex}
  .js .nav{position:absolute;left:0;right:0;top:100%;flex-direction:column;gap:0;padding:8px 24px 20px;background:var(--bg);border-bottom:1px solid var(--line);box-shadow:0 14px 24px rgba(11,31,68,.16);opacity:0;visibility:hidden;translate:0 -8px;transition:opacity .2s ease,translate .2s ease,visibility 0s .2s}
  .js .nav.is-open{opacity:1;visibility:visible;translate:0 0;transition-delay:0s}
  .js .nav a{padding:16px 4px;font-size:1.15rem;border-bottom:1px solid var(--line)}
  .js .nav a::after{display:none}
}
@media (max-width:760px){
  .mobile-bar{position:fixed;left:0;right:0;bottom:0;z-index:40;display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px 14px calc(10px + env(safe-area-inset-bottom,0px));background:var(--bg);border-top:1px solid var(--line);box-shadow:0 -8px 20px rgba(11,31,68,.14)}
  .mobile-bar .btn{width:100%;font-size:1.2rem;animation:none}
  body{padding-bottom:78px}
}

/* ───────── animations (uses `translate`, so existing transforms are untouched) ───────── */
@keyframes rise{from{opacity:0;translate:0 28px}to{opacity:1;translate:0 0}}
@keyframes pop{from{opacity:0;scale:.92}to{opacity:1;scale:1}}
@keyframes bob{0%,100%{translate:0 0}50%{translate:0 -10px}}
@keyframes pulse-ring{0%{box-shadow:0 0 0 0 rgba(107,191,31,.55)}70%{box-shadow:0 0 0 14px rgba(107,191,31,0)}100%{box-shadow:0 0 0 0 rgba(107,191,31,0)}}

/* hero entrance on load */
.hero .hero-left>*,.hero h1,.hero-sub,.hero-actions,.hero-promise,.svc-hero h1,.svc-sub,.svc-hero .hero-actions{animation:rise .7s cubic-bezier(.2,.7,.2,1) both}
.hero-sub,.svc-sub{animation-delay:.12s}
.hero-actions{animation-delay:.24s}
.hero-promise{animation-delay:.34s}
.hero-right{animation:pop .9s cubic-bezier(.2,.7,.2,1) .15s both}
.hero-right img,.hero-right svg{animation:bob 6s ease-in-out 1.2s infinite}

/* header */
.site-header{transition:box-shadow .25s ease}
.site-header.is-scrolled{box-shadow:0 6px 18px rgba(11,31,68,.14)}
.nav a{position:relative}
.nav a::after{content:"";position:absolute;left:0;right:0;bottom:-4px;height:3px;background:var(--green);border-radius:2px;scale:0 1;transform-origin:left;transition:scale .25s ease}
.nav a:hover::after,.nav a:focus-visible::after,.nav a.is-active::after{scale:1 1}

/* buttons and cards */
.btn{transition:translate .18s ease,box-shadow .18s ease,background-color .18s ease,color .18s ease}
.btn:hover{translate:0 -3px;box-shadow:0 8px 16px rgba(11,31,68,.2)}
.btn:active{translate:0 0;box-shadow:none}
.header-actions .btn-primary,.hero-actions .btn-primary{animation:pulse-ring 2.6s ease-out 1.5s infinite}
.svc-card,.price-card,.review,.offer,.step{transition:translate .25s ease,box-shadow .25s ease,opacity .7s ease}
.svc-card:hover,.review:hover,.price-card:hover{translate:0 -6px;box-shadow:0 14px 28px rgba(11,31,68,.18)}
.offer:hover{translate:0 -4px}
.svc-pic{transition:scale .4s ease}
.svc-card{overflow:hidden}
.svc-card:hover .svc-pic{scale:1.05}
.svc-link{transition:letter-spacing .2s ease}
.svc-card:hover .svc-link{letter-spacing:.03em}

/* scroll reveal: classes are added by script.js, so no-JS visitors see everything */
.js-reveal{opacity:0;translate:0 32px;transition:opacity .7s ease,translate .7s cubic-bezier(.2,.7,.2,1)}
.js-reveal.is-visible{opacity:1;translate:0 0}
.js-reveal.is-visible.svc-card:hover,.js-reveal.is-visible.review:hover,.js-reveal.is-visible.price-card:hover{translate:0 -6px}

@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition:none!important}
  .js-reveal{opacity:1;translate:none}
}
"""
write("style.css", css + "\n")

# JS (behaviour only; all content is already in the HTML)
js = r"""document.documentElement.classList.remove('no-js');
document.documentElement.classList.add('js');

(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Mobile menu
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');
  if (toggle && nav) {
    var setMenu = function (open) {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    };
    toggle.addEventListener('click', function () { setMenu(!nav.classList.contains('is-open')); });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) { setMenu(false); } });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { setMenu(false); toggle.focus(); } });
    document.addEventListener('click', function (e) { if (!e.target.closest('.site-header')) { setMenu(false); } });
  }

  // Header shadow once the page is scrolled
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Scroll reveal with a small stagger between siblings
  var revealSel = '.sec-head, .offers-head, .why-head, .team-head, .svc-card, .price-card, .price-note, .offer, ' +
    '.how-panel, .step, .review, .gsummary, .form-card, .faq-item, .locate-info, .paybar-text, .paybar-cta, .chips li';
  var targets = document.querySelectorAll(revealSel);
  if (!reduceMotion && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    targets.forEach(function (el) {
      var sibs = el.parentElement ? Array.prototype.filter.call(el.parentElement.children, function (c) { return c.matches(revealSel); }) : [];
      el.style.transitionDelay = (Math.min(sibs.indexOf(el), 5) * 90) + 'ms';
      el.classList.add('js-reveal');
      io.observe(el);
    });
  }

  // Highlight the nav link of the section in view (home page)
  var navLinks = document.querySelectorAll('.nav a[href*="#"]');
  if ('IntersectionObserver' in window && navLinks.length) {
    var map = {};
    navLinks.forEach(function (a) { map[a.getAttribute('href').split('#')[1]] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var a = map[e.target.id];
        if (a && e.isIntersecting) {
          navLinks.forEach(function (l) { l.classList.remove('is-active'); });
          a.classList.add('is-active');
        }
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    Object.keys(map).forEach(function (id) { var s = document.getElementById(id); if (s) { spy.observe(s); } });
  }

  // FAQ accordion: collapse after load; answers stay in the DOM
  document.querySelectorAll('.faq-item').forEach(function (item) {
    var btn = item.querySelector('.faq-trigger');
    if (!btn) { return; }
    btn.setAttribute('aria-expanded', 'false');
    btn.addEventListener('click', function () {
      var open = item.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  // Team carousel arrows (home page only)
  var track = document.getElementById('team-track');
  document.querySelectorAll('[data-team-scroll]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (!track) { return; }
      var dir = Number(b.getAttribute('data-team-scroll'));
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      track.scrollBy({ left: dir * track.clientWidth * 0.8, behavior: reduce ? 'auto' : 'smooth' });
    });
  });

  // Print a single offer card (home page only)
  function clearPrint() {
    document.querySelectorAll('.offer.printing').forEach(function (el) { el.classList.remove('printing'); });
  }
  window.addEventListener('afterprint', clearPrint);
  document.querySelectorAll('[data-print]').forEach(function (b) {
    b.addEventListener('click', function () {
      var card = b.closest('.offer');
      if (!card) { return; }
      card.classList.add('printing');
      window.print();
      clearPrint();
    });
  });

  // Contact form
  var form = document.getElementById('lead-form');
  if (form) {
    var status = document.getElementById('form-status');
    var btn = form.querySelector('button[type="submit"]');

    // TODO: replace with the real form endpoint (CRM, email service or webhook).
    function sendRequest(data) {
      return new Promise(function (resolve) { setTimeout(resolve, 400); });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      btn.disabled = true;
      btn.textContent = 'Sending…';
      status.className = 'form-status';
      status.textContent = '';
      sendRequest(new FormData(form)).then(function () {
        form.reset();
        status.className = 'form-status ok';
        status.textContent = 'Got it! We’ve received your request and will be in touch shortly.';
      }).catch(function () {
        status.className = 'form-status err';
        status.textContent = 'Something went wrong. Please try again or call us.';
      }).then(function () {
        btn.disabled = false;
        btn.textContent = 'Send request';
      });
    });
  }
})();
"""
write("script.js", js)

# HOME
home_title = pick_title([f"Professional Drain & Plumbing Services{IN} | {BRAND}",
                         f"Drain & Plumbing Services{IN} | {BRAND}", f"Drain Services{IN} | {BRAND}"])
home_url = f"{D}/"
home_nodes = [
    org_node(),
    {"@type": "WebSite", "@id": SITE_ID, "url": f"{D}/", "name": BRAND, "inLanguage": "en", "publisher": {"@id": ORG_ID}},
    webpage_node(home_url, home_title, HOME_DESC, extra={"isPartOf": {"@id": SITE_ID}}),
    {"@type": "ItemList", "@id": f"{home_url}#services", "name": "Drain and plumbing services",
     "itemListElement": [
         {"@type": "ListItem", "position": i,
          "item": {"@type": "Service", "name": nm, "description": ds, "url": f"{D}{URL[k]}", "provider": {"@id": ORG_ID}}}
         for i, (nm, ds, k) in enumerate(SERVICES, 1)]},
    faq_node(home_url, HOME_FAQ),
]
write("index.html", document("/", home_title, HOME_DESC, build_home(), graph(home_nodes)))
written["/"] = (home_title, HOME_DESC)

# SERVICE PAGES
for v in PAGES:
    path = URL[v["key"]]
    title = pick_title(v["titles"])
    v["desc"] = pick_desc(DESC[v["key"]])
    write(path.lstrip("/"), document(path, title, v["desc"], service_main(v), service_graph(v, title, v["desc"]), crumb_name=v["name"]))
    written[path] = (title, v["desc"])

# ABOUT
about_title = f"About {BRAND} | Honest Drain & Plumbing Service"
about_url = f"{D}{URL['about']}"
about_nodes = [org_node(),
               webpage_node(about_url, about_title, ABOUT_DESC, types=("WebPage", "AboutPage"),
                            extra={"breadcrumb": {"@id": f"{about_url}#breadcrumb"}}),
               crumbs_node(about_url, "About")]
write("about.html", document(URL["about"], about_title, ABOUT_DESC, about_main(), graph(about_nodes), crumb_name="About"))
written[URL["about"]] = (about_title, ABOUT_DESC)

# 404
write("404.html", document("/404.html", f"Page Not Found | {BRAND}", "The page you are looking for doesn’t exist or has moved. Browse our drain and plumbing services.", build_404(), None, noindex=True))

# robots.txt
write("robots.txt", f"""# {BRAND}: robots.txt
User-agent: *
Allow: /

# AI crawlers are welcome
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: {D}/sitemap.xml
""")

# sitemap.xml
prio = {"/": ("weekly", "1.0")}
for p in URL.values():
    prio[p] = ("monthly", "0.8") if p != URL["about"] else ("yearly", "0.5")
urls = ["/"] + [URL[k] for k in ("drain-cleaning", "sewer-backup", "emergency-plumbing", "leak-detection", "about")]
sm = ['<?xml version="1.0" encoding="UTF-8"?>', f"<!-- {BRAND}: sitemap.xml -->",
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for p in urls:
    cf, pr = prio[p]
    sm.append(f"  <url>\n    <loc>{D}{p}</loc>\n    <lastmod>{C['DATE_MODIFIED']}</lastmod>\n    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>")
sm.append("</urlset>")
write("sitemap.xml", "\n".join(sm) + "\n")

# .htaccess
write(".htaccess", f"""# {BRAND}: Apache configuration
Options -Indexes
DirectoryIndex index.html
AddDefaultCharset UTF-8

# 404 page
ErrorDocument 404 /404.html

# GZIP
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css text/plain text/xml application/xml application/javascript application/json application/ld+json image/svg+xml
</IfModule>

# Browser caching
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresDefault "access plus 1 week"
  ExpiresByType text/html "access plus 0 seconds"
  ExpiresByType text/css "access plus 1 month"
  ExpiresByType application/javascript "access plus 1 month"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/webp "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType application/xml "access plus 1 day"
  ExpiresByType text/plain "access plus 1 day"
</IfModule>

# Security headers
<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set X-Frame-Options "SAMEORIGIN"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
""")

# favicon.svg (brand drop)
write("favicon.svg", '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 78"><path d="M30 2C30 2 4 36 4 56a26 26 0 0 0 52 0C56 36 30 2 30 2Z" fill="#0B2A5B"/><path d="M17 58a13 13 0 0 0 13 13" fill="none" stroke="#6BBF1F" stroke-width="5" stroke-linecap="round"/></svg>
''')

# logo.svg: tightened copy of the supplied logo (same artwork, margins cropped)
logo = open(LOGO_SVG, encoding="utf-8").read()
logo = logo.replace('width="1400" height="1020" viewBox="0 0 1400 1020"', 'width="1380" height="900" viewBox="10 90 1380 900"', 1)
assert 'viewBox="10 90 1380 900"' in logo
write("logo.svg", logo)

# logo.png + og-image.png (needs: pip install cairosvg pillow; existing PNGs are kept if missing)
try:
    import cairosvg
    from PIL import Image
    cairosvg.svg2png(bytestring=logo.encode(), write_to=os.path.join(OUT, "logo.png"), output_width=600)
    tmp = os.path.join(OUT, "_tmp_logo.png")
    cairosvg.svg2png(bytestring=logo.encode(), write_to=tmp, output_height=520)
    lg = Image.open(tmp).convert("RGBA")
    canvas = Image.new("RGB", (1200, 630), "white")
    canvas.paste(lg, ((1200 - lg.width) // 2, (630 - lg.height) // 2), lg)
    canvas.save(os.path.join(OUT, "og-image.png"), optimize=True)
    os.remove(tmp)

except ImportError:
    print("cairosvg/Pillow not installed: logo.png and og-image.png were not regenerated")

# report
print("pages:", len(written) + 1)
for p, (t, d) in written.items():
    print(f"{p:28} title={len(t):2}  desc={len(d):3}")
