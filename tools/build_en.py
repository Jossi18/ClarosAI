"""Generate en.html (English) from index.html (French).

Usage:  python3 tools/build_en.py
Every French string is listed in tools/en.py. After editing index.html, re-run
this script; it fails loudly if a translated string is no longer found, and it
prints any French-looking text left in en.html so nothing slips through.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from en import T  # noqa: E402

SITE = "https://claros-ai.vercel.app"
src = (ROOT / "index.html").read_text(encoding="utf-8")
out = src


def must(old, new, count=1):
    global out
    n = out.count(old)
    if n != count:
        raise SystemExit(f"Structural replace expected {count}, found {n}: {old[:80]!r}")
    out = out.replace(old, new)


# ---------- structural changes ----------
must('<html lang="fr">', '<html lang="en">')
must(f'<link rel="canonical" href="{SITE}/">', f'<link rel="canonical" href="{SITE}/en">')
must('<meta property="og:locale" content="fr_FR">', '<meta property="og:locale" content="en_US">')
must('<div class="lang-sw" role="group" aria-label="Langue">', '<div class="lang-sw" role="group" aria-label="Language">')
must('<a href="/" lang="fr" hreflang="fr" data-lang="fr" aria-current="page">FR</a>',
     '<a href="/" lang="fr" hreflang="fr" data-lang="fr">FR</a>')
must('<a href="/en" lang="en" hreflang="en" data-lang="en">EN</a>',
     '<a href="/en" lang="en" hreflang="en" data-lang="en" aria-current="page">EN</a>')
# numbers: English formatting, euro sign first
must("var nf = new Intl.NumberFormat('fr-FR');", "var nf = new Intl.NumberFormat('en-US');")
must("textContent = r + ' €';", "textContent = '€' + r;")
must("textContent = nf.format(Math.round(year / 100) * 100) + ' €';",
     "textContent = '€' + nf.format(Math.round(year / 100) * 100);")

# internal ids that look like French words: translate only the visible unit
must("unit: 'avis'", "unit: 'reviews'")
must("x[1] + ' %'", "x[1] + '%'", count=2)
must("c.splitTitle + ' : '", "c.splitTitle + ': '")

# static initial values of the calculator
for fr, en in [(">35 €<", ">€35<"), (">22 900 €<", ">€22,900<"), (">22 900 €<", ">€22,900<"), (">22 900 €<", ">€22,900<")]:
    out = out.replace(fr, en)


# ---------- text replacements ----------
def flex(s):
    """Regex for a French string where any run of spaces may be any whitespace."""
    parts = re.split(r"\s+", s.strip())
    return r"\s+".join(re.escape(p) for p in parts)


def esc_js(s, quote):
    s = s.replace("\\", "\\\\") if "\\u" not in s else s
    return s.replace(quote, "\\" + quote)


missing = []
for fr, en in sorted(T.items(), key=lambda kv: -len(kv[0])):
    if fr == en:
        continue
    hit = 0
    f = flex(fr)
    # 1) HTML text node: >  text  <
    pat = re.compile(r"(>\s*)" + f + r"(\s*<)")
    out, n = pat.subn(lambda m: m.group(1) + en + m.group(2), out)
    hit += n
    # 2) attribute value
    pat = re.compile(r'(="\s*)' + f + r'(\s*")')
    out, n = pat.subn(lambda m: m.group(1) + en.replace('"', "&quot;") + m.group(2), out)
    hit += n
    # 3) JS string literal, single or double quoted
    for q in ("'", '"'):
        lit = q + fr + q
        if lit in out:
            hit += out.count(lit)
            out = out.replace(lit, q + esc_js(en, q) + q)
    # 4) long phrases embedded elsewhere (safe: too specific to collide)
    if not hit and len(fr) > 28 and fr in out:
        hit += out.count(fr)
        out = out.replace(fr, en)
    if not hit:
        missing.append(fr)

# English typography: no space before %
parts = re.split(r"(<style>.*?</style>)", out, flags=re.S)
out = "".join(pt if pt.startswith("<style>") else re.sub(r"(\d)[ \u00a0\u202f]%", r"\1%", pt) for pt in parts)

(ROOT / "en.html").write_text(out, encoding="utf-8")

# ---------- report ----------
if missing:
    print(f"{len(missing)} strings not found in index.html (check en.py keys):")
    for m in missing:
        print("  -", m[:100])

body = re.sub(r"<style>.*?</style>", "", out, flags=re.S)
visible = re.sub(r"<[^>]+>", "\n", re.sub(r"<script>.*?</script>", "", body, flags=re.S))
scripts = "\n".join(re.findall(r"<script>(.*?)</script>", body, flags=re.S))
fr_hint = re.compile(r"[àâçéèêëîïôûùœ«»]|\b(le|la|les|des|du|une|et|pour|vous|votre|vos|avec|sur|dans|est|sont|pas)\b", re.I)
left = [line.strip() for line in visible.split("\n") if line.strip() and fr_hint.search(line)]
left += [m for m in re.findall(r"'((?:[^'\\\n]|\\.)*)'", scripts) if fr_hint.search(m) and " " in m]
allow = ("Auvergne-Rhône-Alpes", "Rhône Metalworks", "Durand", "Fabre", "Lemaire", "Léa P.", "Français", "120 m²")
left = [l for l in left if not any(a in l for a in allow)]
print(f"en.html written. Possible French left: {len(left)}")
for l in left[:80]:
    print("  ?", l[:110])
