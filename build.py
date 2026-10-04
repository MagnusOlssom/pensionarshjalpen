#!/usr/bin/env python3
"""Bygger Pensionärshjälpens statiska sajt till docs/ (GitHub Pages).

Kör:  python3 build.py
Innehåll: content/*.md  (en fil = en undersida)
Utseende: src/style.css
"""
import html
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
CONTENT = ROOT / "content"

# Byt till https://pensionarshjalpen.se när domänen är kopplad (och lägg en CNAME-fil i src/).
SITE_URL = "https://xn--pensionrshjlpen-6kbe.se"  # = pensionärshjälpen.se
NAME = "Pensionärshjälpen"
PHONE_DISPLAY = "0704-32 69 24"
PHONE_TEL = "+46704326924"

# ---------- små byggstenar ----------

LOGO = """<svg viewBox="0 0 48 48" aria-hidden="true" focusable="false">
<path d="M24 3C12.4 3 3 11.2 3 21.3c0 5.6 2.9 10.6 7.5 14L8.6 44.2a1 1 0 0 0 1.5 1.1l9.3-6c1.5.3 3 .4 4.6.4 11.6 0 21-8.2 21-18.4S35.6 3 24 3Z" fill="#c2335c"/>
<path d="M24 31.5s-9-5.4-9-11.2a4.9 4.9 0 0 1 9-2.8 4.9 4.9 0 0 1 9 2.8c0 5.8-9 11.2-9 11.2Z" fill="#fff"/>
</svg>"""

PHONE_ICON = """<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1L6.6 10.8Z"/></svg>"""

CLOUDS = """<svg class="cloud a" viewBox="0 0 200 90" aria-hidden="true" focusable="false"><path d="M45 85a40 40 0 0 1-3-80 50 50 0 0 1 93 8 36 36 0 0 1 22 72Z"/></svg>
<svg class="cloud b" viewBox="0 0 200 90" aria-hidden="true" focusable="false"><path d="M45 85a40 40 0 0 1-3-80 50 50 0 0 1 93 8 36 36 0 0 1 22 72Z"/></svg>"""


def esc(s):
    return html.escape(s, quote=True)


COST_NOTE = "Just nu kostar hjälpen ingenting."


def call_box(note=True):
    """Samma ring-ruta överallt: ett vitt kort med numret. Pekskärm = knapp, dator = stort nummer."""
    extra = ""
    if note:
        extra = f"""
  <p class="call-note">En vänlig människa svarar. Ingen robot, inga knappval.</p>
  <p class="call-cost">{COST_NOTE}</p>"""
    return f"""<div class="call">
  <a class="call-button" href="tel:{PHONE_TEL}">{PHONE_ICON}<span><span class="small">Tryck här, så ringer du oss</span><span class="num">{PHONE_DISPLAY}</span></span></a>
  <div class="call-desk">
    <p class="label">Ring det här numret:</p>
    <p class="big">{PHONE_DISPLAY}</p>
  </div>{extra}
</div>"""


def eyebrow(text):
    """Liten etikett ovanför rubriken – ger sidan rytm och berättar vad avsnittet handlar om."""
    return f'<p class="eyebrow">{esc(text)}</p>'


def portrait(up, size="small"):
    """Porträttet av Magnus. Bygget krymper bilden (se main)."""
    return (f'<img class="portrait {size}" src="{up}magnus.jpg" width="520" height="595" '
            f'alt="Magnus, som startade Pensionärshjälpen, står vid vattnet och ler.">')


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


def heading(s):
    """Rubriktext: namnet får en mjuk avstavning så det inte bryts mitt i ordet på en smal mobil."""
    return inline(s).replace("Pensionärshjälpen", "Pensionärs&shy;hjälpen")


def md(text):
    """Minimal markdown: ## rubrik, - lista, 1. lista, stycken, :::tip / :::warn-rutor."""
    out, para, items, kind = [], [], [], None

    def flush():
        nonlocal para, items, kind
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para = []
        if items:
            tag = "ol" if kind == "ol" else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>")
            items, kind = [], None

    for line in text.splitlines():
        s = line.strip()
        if s.startswith(":::"):
            flush()
            box = s[3:].strip()
            out.append(f'<div class="{box}">' if box else "</div>")
        elif s.startswith("## "):
            flush()
            out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("- "):
            if para or kind == "ol":
                flush()
            kind = "ul"
            items.append(s[2:])
        elif re.match(r"^\d+\. ", s):
            if para or kind == "ul":
                flush()
            kind = "ol"
            items.append(re.sub(r"^\d+\. ", "", s))
        elif not s:
            flush()
        else:
            if items:
                flush()
            para.append(s)
    flush()
    return "\n".join(out)


def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    meta["body"] = m.group(2)
    meta["slug"] = path.stem
    meta.setdefault("order", "999")
    return meta


def page(*, title, description, path, body, depth, schema=None):
    """depth = antal mappnivåer under roten (för relativa länkar)."""
    up = "../" * depth
    canonical = SITE_URL + "/" + path
    ld = ""
    if schema:
        ld = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False) + "</script>"
    return f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="sv_SE">
<meta name="theme-color" content="#cdebf7">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{up}favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
<link rel="manifest" href="{up}site.webmanifest">
<link rel="preload" href="{up}fonts/atkinson-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{up}style.css">
{ld}
</head>
<body>
{body}
</body>
</html>
"""


def brand(depth=0):
    """Namnet uppe till höger. Länk till startsidan (Magnus önskemål)."""
    return f'<a class="brand" href="{"../" * depth if depth else "./"}" aria-label="Till startsidan">{NAME}{LOGO}</a>'


def grouped(topics):
    """Ämnena grupperade efter `group` i innehållets front matter, dolda sidor borträknade."""
    groups = {}
    for t in topics:
        if t.get("hidden") == "yes":
            continue
        groups.setdefault(t.get("group", "Övrigt"), []).append(t)
    return groups


def index_list(topics, up, cls="more"):
    return f'<ul class="{cls}">' + "".join(
        f'<li><a href="{up}{t["slug"]}/">{esc(t["link"])}</a></li>' for t in topics) + "</ul>"


def footer(depth, topics, home=False, here=""):
    up = "../" * depth
    items = []
    if not home:
        items.append(("./", "Till startsidan"))
    if here != "om":
        items.append(("om/", "Om Pensionärshjälpen"))
    links = "".join(f'<li><a href="{up}{h}">{t}</a></li>' for h, t in items)
    groups = "".join(
        f'<div class="index-group"><h3>{esc(g)}</h3>{index_list(ts, up, "index")}</div>'
        for g, ts in grouped(topics).items())
    return f"""<footer class="block sky">
<div class="inner">
<ul class="more foot-nav">{links}</ul>
<nav class="index-wrap" aria-labelledby="alla-amnen">
{eyebrow("Läs mer")}
<h2 id="alla-amnen">Alla ämnen</h2>
<div class="index-groups">{groups}</div>
</nav>
<div class="foot-meta">
<p><strong>{NAME}</strong> – en människa som svarar<br>Telefon: {PHONE_DISPLAY}<br>Magnus Olsson</p>
<p>Den här sidan använder inga kakor (cookies) och samlar inte in något om dig. Du kan läsa i lugn och ro.</p>
</div>
</div>
</footer>"""


ORG_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": NAME,
    "url": SITE_URL + "/",
    "telephone": PHONE_TEL,
    "areaServed": "SE",
    "knowsLanguage": "sv",
    "description": "Telefonhjälp för äldre med det digitala: BankID, Swish, appar, deklarationen, 1177, Kivra och köp på nätet.",
}

# ---------- sidor ----------


def lower_group(g):
    """Gemener i rubriken, men BankID behåller sina versaler."""
    g = re.sub(r"^Om ", "", g)
    if g.startswith("BankID"):
        return g
    return g[0].lower() + g[1:]


def build_topic(meta, all_topics):
    body_html = md(meta["body"])
    faq = None
    if meta.get("faq_q"):
        faq = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{
                "@type": "Question",
                "name": meta["faq_q"],
                "acceptedAnswer": {"@type": "Answer", "text": meta["faq_a"]},
            }],
        }
    rel = [t for t in all_topics if t.get("group") == meta.get("group") and t["slug"] != meta["slug"] and t.get("hidden") != "yes"][:4]
    related = ""
    if rel:
        lis = "".join(f'<li><a href="../{t["slug"]}/">{esc(t["link"])}</a></li>' for t in rel)
        related = f"""<section class="block paper"><div class="inner">
{eyebrow("Läs mer")}
<h2>Mer om {esc(lower_group(meta['group']))}</h2>
<ul class="more">{lis}</ul>
</div></section>"""
    # `photo: yes` i front matter visar porträttet i sidhuvudet. Om-sidan får det alltid.
    has_photo = meta.get("photo") == "yes" or meta["slug"] == "om"
    photo = f'<div class="hero-photo">{portrait("../", "large")}</div>' if has_photo else ""
    body = f"""<main>
<section class="block {meta.get('color', 'sky')} hero{' has-photo' if has_photo else ''}">
{CLOUDS}
<div class="inner">
{brand(1)}
<div class="hero-grid">
<div class="hero-text">
{photo}
<h1>{heading(meta["h1"])}</h1>
<p class="lead">{inline(meta['lead'])}</p>
</div>
{call_box()}
</div>
</div>
</section>
<section class="block paper">
<div class="inner article">
{body_html}
</div>
</section>
<section class="block mint">
<div class="inner">
{eyebrow("Ring oss")}
<h2>Vill du ha hjälp med det här?</h2>
<p>Ring oss, så tar vi det i din takt. Du behöver inte ha läst klart.</p>
{call_box(note=False)}
</div>
</section>
{related}
</main>
{footer(1, all_topics, here=meta["slug"])}"""
    return page(
        title=meta["title"], description=meta["description"],
        path=meta["slug"] + "/", body=body, depth=1, schema=faq,
    )


def build_home(topics):
    more = "\n".join(
        f'<li><a href="{t["slug"]}/">{esc(t["link"])}</a></li>' for t in topics if t.get("home") == "yes"
    ) + '\n<li><a href="amnen/">Alla ämnen</a></li>'
    body = f"""<main>
<section class="block sky hero">
{CLOUDS}
<div class="inner">
{brand()}
<div class="hero-grid">
<div class="hero-text">
<h1>Fastnat med mobilen eller datorn?</h1>
<p class="lead">Ring oss, så svarar en människa som har tid. Vi tar det i din takt, ett steg i taget.</p>
</div>
{call_box()}
</div>
<a class="scroll-hint" href="#mer">Läs mer <span aria-hidden="true">↓</span></a>
</div>
</section>

<section class="block sun" id="mer">
<div class="inner">
{eyebrow("Vad vi hjälper till med")}
<h2>Du kan ringa om det mesta som krånglar</h2>
<ul class="plain-list">
<li>BankID och Swish</li>
<li>Appar som inte vill fungera</li>
<li>Deklarationen hos Skatteverket</li>
<li>1177, recept och vårdbesök</li>
<li>Kivra och brev som kommer i mobilen</li>
<li>Att köpa något på nätet</li>
<li>Rutor om kakor, villkor och avtal</li>
<li>Sms och samtal som känns konstiga</li>
<li>Texten som är för liten</li>
</ul>
<p>Är du osäker på om det här är något vi kan hjälpa till med? Ring ändå, så tar vi reda på det tillsammans.</p>
</div>
</section>

<section class="block rose">
<div class="inner">
{eyebrow("Steg för steg")}
<h2>Så går det till</h2>
<ol class="steps">
<li>Du ringer, när det passar dig.</li>
<li>Du berättar vad du ser på skärmen. Du behöver inte veta vad saker heter.</li>
<li>Vi tar det tillsammans, ett steg i taget, tills det fungerar. Ingen fråga är för liten.</li>
</ol>
</div>
</section>

<section class="block paper">
<div class="inner">
<div class="promise">
{eyebrow("Tänk på din säkerhet")}
<h2>Det här gör vi aldrig</h2>
<ul>
<li>Vi frågar aldrig efter din kod till BankID, banken eller kortet.</li>
<li>Vi ber dig aldrig att logga in med BankID åt oss.</li>
<li>Vi ber dig aldrig att föra över pengar.</li>
<li>Vi ringer aldrig upp dig utan att du har bett om det.</li>
</ul>
<p>Om någon som säger att de är från oss ber om något av det här: lägg på.</p>
</div>
</div>
</section>

<section class="block mint">
<div class="inner">
<div class="about">
{portrait("")}
<div class="about-text">
{eyebrow("Vem svarar?")}
<h2>Jag som svarar</h2>
<p>Hej, jag heter Magnus. Jag startade Pensionärshjälpen för att en närstående så ofta fastnade med tekniken och aldrig fick tag i en människa att fråga.</p>
<p>Nu kan du ringa i stället.</p>
<p class="about-link"><a href="om/">Mer om Pensionärshjälpen</a></p>
</div>
</div>
{eyebrow("Ring oss")}
<h2>Ring när det krånglar</h2>
{call_box()}
</div>
</section>

<section class="block paper">
<div class="inner">
{eyebrow("Vanliga frågor")}
<h2>Läs mer</h2>
<p>Här kan du läsa mer om sådant vi ofta hjälper till med. Du behöver inte läsa något innan du ringer.</p>
<ul class="more">
{more}
</ul>
</div>
</section>
</main>
{footer(0, topics, home=True)}"""
    return page(
        title=f"{NAME} – en människa som svarar när mobilen, datorn eller BankID krånglar",
        description=f"Krånglar BankID, Swish, en app eller deklarationen? Ring {PHONE_DISPLAY}. En vänlig människa svarar, har tid och hjälper dig steg för steg. Just nu kostar hjälpen ingenting.",
        path="", body=body, depth=0, schema=ORG_SCHEMA,
    )


def build_amnen(topics):
    parts = "".join(
        f'<section class="topic-group"><h2>{esc(g)}</h2>{index_list(ts, "../")}</section>'
        for g, ts in grouped(topics).items())
    body = f"""<main>
<section class="block sun hero">
{CLOUDS}
<div class="inner">
{brand(1)}
<div class="hero-grid">
<div class="hero-text">
<h1>Det här brukar vi hjälpa till med</h1>
<p class="lead">Hittar du inte det du letar efter? Ring ändå, så tar vi reda på det tillsammans.</p>
</div>
{call_box()}
</div>
</div>
</section>
<section class="block paper">
<div class="inner">
{eyebrow("Alla ämnen")}
{parts}
</div>
</section>
</main>
{footer(1, topics, here="amnen")}"""
    return page(
        title=f"Alla ämnen – {NAME}",
        description=f"BankID, Swish, Kivra, 1177, deklarationen, bedrägerier och mer. Ring {PHONE_DISPLAY} så hjälper en vänlig människa dig.",
        path="amnen/", body=body, depth=1,
    )


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "src" / "fonts", OUT / "fonts")
    for f in (ROOT / "src").iterdir():
        if f.is_file():
            shutil.copy(f, OUT / f.name)
    # Porträttet visas som mest ~260 px brett, så 520 px räcker (skarpt även på "retina").
    # Krymper med macOS-verktyget sips om det finns – annars används originalet som det är.
    try:
        subprocess.run(["sips", "-Z", "520", "-s", "format", "jpeg", "-s", "formatOptions", "78",
                        str(ROOT / "src" / "magnus.jpg"), "--out", str(OUT / "magnus.jpg")],
                       check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        pass
    (OUT / "favicon.svg").write_text(LOGO.replace(' aria-hidden="true" focusable="false"', ' xmlns="http://www.w3.org/2000/svg"'), encoding="utf-8")
    (OUT / ".nojekyll").write_text("")

    topics = sorted((parse(p) for p in CONTENT.glob("*.md")), key=lambda t: (int(t["order"]), t["link"]))
    (OUT / "index.html").write_text(build_home([t for t in topics if t.get("hidden") != "yes"]), encoding="utf-8")
    for t in topics:
        d = OUT / t["slug"]
        d.mkdir()
        (d / "index.html").write_text(build_topic(t, topics), encoding="utf-8")

    (OUT / "amnen").mkdir()
    (OUT / "amnen" / "index.html").write_text(build_amnen(topics), encoding="utf-8")

    today = date.today().isoformat()
    urls = [SITE_URL + "/", SITE_URL + "/amnen/"] + [f"{SITE_URL}/{t['slug']}/" for t in topics]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
        + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"Byggt {len(topics)} undersidor + startsida till {OUT}")


if __name__ == "__main__":
    main()
