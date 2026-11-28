"""Shared CSS and page shell. Tokens match vault/design-notes.md (research-report look)."""

CSS = """
:root{
  --paper:#FFFFFF;--surface:#F4F5F3;--ink:#15191E;--ink-2:#525A63;--rule:#D9DCDF;
  --brand:#1B3A5C;--pop:#0FB3C8;--pop-fill:#D5F4F8;
  --safe:#2F6B4F;--watch:#9A6212;--risk:#A23B2C;--safe-bg:#E8F0EB;--watch-bg:#F6EEDF;--risk-bg:#F5E4E1;
  --serif:"Source Serif 4",Georgia,serif;--sans:"Libre Franklin","Helvetica Neue",Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#121518;--surface:#191D21;--ink:#E7E9EA;--ink-2:#9AA2AA;--rule:#2B3137;--brand:#9DBCDD;
  --pop:#3CCFE0;--pop-fill:#11373D;--safe:#79B394;--watch:#D6A452;--risk:#E2806F;
  --safe-bg:#1B2A22;--watch-bg:#2C2416;--risk-bg:#2E1C19;color-scheme:dark}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 var(--sans);font-variant-numeric:tabular-nums}
.wrap{max-width:1040px;margin:0 auto;padding:0 max(16px,env(safe-area-inset-left))}
a{color:var(--brand)} a:hover{text-decoration-thickness:2px}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.01em;line-height:1.15;text-wrap:balance}
h1{font-size:clamp(1.8rem,4vw,2.6rem);margin:.2em 0 .3em}
h2{font-size:1.35rem;margin:0 0 .5em}
p{max-width:68ch}
.dim{color:var(--ink-2)} .mono{font-family:var(--mono);font-size:.85em}
.label{font:500 .72rem/1.2 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2)}
.mast{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px 24px;padding:18px 0;border-bottom:1px solid var(--rule)}
.word{display:flex;align-items:center;gap:9px;font:600 1.35rem var(--serif);color:var(--ink);text-decoration:none}
.nav{display:flex;flex-wrap:wrap;gap:20px;font-size:.92rem}
.nav a{color:var(--ink-2);text-decoration:none} .nav a.on,.nav a:hover{color:var(--ink);box-shadow:inset 0 -2px 0 var(--brand)}
section{border-top:1px solid var(--rule);padding:32px 0;display:grid;gap:14px}
section:first-of-type{border-top:0}
.hl{background:var(--pop-fill);box-shadow:inset 0 -2px 0 var(--pop);padding:0 .15em}
.tbl{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th{font:500 .7rem var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2);text-align:left;padding:7px 8px;border-bottom:1px solid var(--ink);white-space:nowrap}
td{padding:7px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
td.n,th.n{text-align:right} tr:hover td{background:var(--surface)}
.read{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.read::before{content:"";width:8px;height:8px;background:var(--c,var(--ink-2));flex:none}
td.why{width:38%;min-width:120px}td.why .read{white-space:normal}.sub{display:block;font-size:.82rem;color:var(--ink-2);margin-top:2px}.bar{display:block;height:6px;background:var(--rule);margin-top:6px;max-width:160px}.bar span{display:block;height:6px}
.big{font-size:1.5rem;font-weight:600}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0;border-top:1px solid var(--rule)}
.stat{padding:14px 16px 14px 0;border-bottom:1px solid var(--rule)}
.stat .v{font:600 1.9rem var(--sans);display:block}
.note{font-size:.8rem;color:var(--ink-2);border-top:1px solid var(--rule);padding-top:8px}
.banner{border-left:3px solid var(--risk);background:var(--risk-bg);padding:10px 14px}
.flags{list-style:none;padding:0;margin:0;display:grid}
.flags li{padding:9px 0;border-bottom:1px solid var(--rule);display:grid;grid-template-columns:130px minmax(0,1fr);gap:14px}
@media (max-width:560px){.flags li{grid-template-columns:1fr;gap:2px}}
.chip{font-size:.75rem;font-weight:500;padding:2px 7px;border-radius:2px;color:var(--c);background:var(--cb);justify-self:start}
input,select{font:inherit;color:var(--ink);background:var(--paper);border:1px solid var(--rule);border-radius:2px;padding:7px 9px}
input:focus-visible,select:focus-visible,a:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
.search{position:relative;max-width:520px}
.search input{width:100%;font-size:1rem;padding:10px 12px}
.results{position:absolute;left:0;right:0;top:100%;background:var(--paper);border:1px solid var(--rule);border-top:0;z-index:5;max-height:320px;overflow:auto}
.results a{display:flex;justify-content:space-between;gap:12px;padding:8px 12px;text-decoration:none;color:var(--ink);border-bottom:1px solid var(--rule)}
.results a:hover,.results a:focus{background:var(--surface)}
svg text{fill:var(--ink-2);font:11px var(--sans)}
footer{border-top:1px solid var(--rule);margin-top:40px;padding:20px 0 40px;font-size:.82rem;color:var(--ink-2)}
.filters{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:end}
.filters label{display:grid;gap:4px;font-size:.78rem;color:var(--ink-2)}
button{font:inherit;border:1px solid var(--brand);background:var(--brand);color:var(--paper);padding:7px 12px;border-radius:2px;cursor:pointer}
.btn{font:500 .85rem var(--sans);color:var(--ink);background:var(--paper);border:1px solid var(--ink);border-radius:2px;padding:7px 12px;cursor:pointer}.btn:hover{background:var(--surface)}
.watchbox{display:flex;flex-wrap:wrap;gap:10px;align-items:center}.controls{display:flex;flex-wrap:wrap;gap:16px;align-items:center;margin:12px 0}
td.ind{max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis} td.d{white-space:nowrap} .filters select{max-width:240px}
.lede{font-size:1.15rem;line-height:1.5;color:var(--ink)}ul.cases{list-style:none;padding:0;margin:0}ul.cases li{padding:12px 0;border-bottom:1px solid var(--rule)}
th.sort{cursor:pointer} th.sort:hover{color:var(--ink)}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600'
         '&family=Libre+Franklin:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">')

LOGO = ('<svg width="24" height="16" viewBox="0 0 26 18" aria-hidden="true"><path d="M1 6 H12 M14 12 H25" stroke="var(--brand)" '
        'stroke-width="2.4" fill="none"/><path d="M12 6 L14 12" stroke="var(--pop)" stroke-width="2.4" fill="none"/></svg>')

SITE_URL = "https://mahirzmansuri-hash.github.io/earnings-scanner/"
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 26 18'%3E%3Cpath d='M1 6H12M14 12H25' "
           "stroke='%231B3A5C' stroke-width='3' fill='none'/%3E%3Cpath d='M12 6L14 12' stroke='%230FB3C8' stroke-width='3'/%3E%3C/svg%3E")

# Visitor counting (both public values, not secrets). Empty = nothing added to the pages.
GOATCOUNTER_CODE = "earnings-scanner"      # the "code" from your GoatCounter site, e.g. "faultline" for faultline.goatcounter.com
GOOGLE_VERIFY = "0y-kCoVvvh4MC3Wdy95sWzlH9-NbOiAGvy2Z5zdPrm0"         # Search Console "HTML tag" method: just the content="..." value


def head_extras() -> str:
    out = ""
    if GOOGLE_VERIFY:
        out += f'<meta name="google-site-verification" content="{GOOGLE_VERIFY}">'
    if GOATCOUNTER_CODE:   # cookie-free page counts; no personal data stored
        out += f'<script data-goatcounter="https://{GOATCOUNTER_CODE}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>'
    return out


# Buttondown newsletter username (public, not a secret). Empty = no sign-up box anywhere on the site.
NEWSLETTER_USER = "mahir"


def subscribe_box() -> str:
    """Email sign-up for the weekly digest. A plain HTML form posting to Buttondown (no scripts, no tracking)."""
    if not NEWSLETTER_USER:
        return ""
    return (f'<form class="watchbox" action="https://buttondown.com/api/emails/embed-subscribe/{NEWSLETTER_USER}" method="post">'
            '<label for="bd-email">Get the weekly digest by email</label>'
            '<input type="email" name="email" id="bd-email" placeholder="you@example.com" required>'
            '<button type="submit">Subscribe</button><span class="dim">Free. One email a week. Unsubscribe any time.</span></form>')


NAV = [("index.html", "Home"), ("new.html", "New filings"), ("alerts.html", "Alerts"), ("receipts.html", "Receipts"), ("screener.html", "Screener"), ("track-record.html", "Track record"),
       ("methodology.html", "Methodology"), ("about.html", "About")]


def page(title: str, body: str, description: str, root: str = "", active: str = "", image: str = "og.png") -> str:
    nav = "".join(f'<a href="{root}{href}"{" class=on" if href == active else ""}>{name}</a>' for href, name in NAV)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{description}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{description}">
<meta property="og:type" content="website"><meta property="og:image" content="{SITE_URL}{image}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE_URL}{image}">
<link rel="icon" href="{FAVICON}">
<link rel="alternate" type="application/atom+xml" title="Faultline alerts" href="{SITE_URL}feed.xml">
{FONTS}{head_extras()}<style>{CSS}</style></head><body><div class="wrap">
<header class="mast"><a class="word" href="{root}index.html">{LOGO}Faultline</a><nav class="nav" aria-label="Main">{nav}</nav></header>
<main>{body}</main>
<footer>Faultline is research, not investment advice. Data: SEC EDGAR filings (free public data).
Scores use only information that was public on each filing date.
<a href="{root}methodology.html">How it works</a> · <a href="{root}about.html">About</a></footer>
</div></body></html>"""
