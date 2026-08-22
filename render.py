"""HTML-generator for FPL-tavla.

Samme strukturelle grep som VM-tavla (flytende vh-skalering for TV, kortbasert
ledertavle, gull/soelv/bronse paa topp tre), men Premier League-paletten i stedet
for den roede VM-bakgrunnen.
"""

from html import escape

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    "family=Barlow:wght@400;600;700&"
    "family=Barlow+Condensed:wght@600;700;800&"
    "family=Spline+Sans+Mono:wght@600;700&display=swap\" rel=\"stylesheet\">"
)

CSS = """
  :root {
    --surface: rgba(45, 8, 62, 0.88);
    --surface-hover: rgba(64, 14, 86, 0.95);
    --chalk: #f6f2fa;
    --muted: #bda4d0;
    --line: rgba(246, 242, 250, 0.18);
    --divider: rgba(246, 242, 250, 0.09);
    --gronn: #00ff87;
    --cyan: #04f5ff;
    --rosa: #e90052;
    /* Nedpil: roed, men lysnet - ren #f00 vibrerer mot den lilla bakgrunnen. */
    --ned: #ff4d4d;
    --gold: #f6c453;
    --silver: #dcd6e2;
    --bronze: #e0a070;
    --display: "Barlow Condensed", "Arial Narrow", sans-serif;
    --body: "Barlow", system-ui, sans-serif;
    --digits: "Spline Sans Mono", ui-monospace, monospace;
  }

  /* Flytende rot-skala: header + 9-12 rader skal fylle TV-en uten aa gaa i overflow.
     1.62vh er maalt mot 1920x1080 med 9 rader + header + footer; vw-leddet er en
     sikring paa smale/staaende skjermer. */
  html { font-size: clamp(15px, min(1.62vh, 1.45vw), 38px); }
  * { box-sizing: border-box; }

  body {
    margin: 0;
    min-height: 100vh;
    color: var(--chalk);
    font-family: var(--body);
    background:
      radial-gradient(55rem 38rem at 88% -12%, #6d0a7a 0%, transparent 62%),
      radial-gradient(48rem 34rem at -5% 20%, #2b0b5e 0%, transparent 58%),
      linear-gradient(180deg, #3d0148 0%, #240132 70%, #16021f 100%);
    background-attachment: fixed;
  }

  .wrap { position: relative; max-width: 82rem; margin: 0 auto; padding: 1.5rem 1.5rem 1.2rem; }

  header { margin-bottom: 1.1rem; }
  .head-grid {
    display: flex; justify-content: space-between; align-items: flex-end;
    gap: 1.5rem; flex-wrap: wrap;
  }

  .eyebrow {
    display: flex; align-items: center; gap: 0.9rem; flex-wrap: wrap;
    font-family: var(--display); font-weight: 600;
    font-size: 1rem; letter-spacing: 0.3em; text-transform: uppercase;
    color: var(--cyan);
    margin-bottom: 0.45rem;
  }
  .status {
    display: inline-flex; align-items: center; gap: 0.45rem;
    color: var(--gronn); letter-spacing: 0.14em;
    background: rgba(0, 255, 135, 0.12);
    border: 1px solid rgba(0, 255, 135, 0.38);
    padding: 0.15rem 0.65rem; border-radius: 999px;
  }
  .status .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--gronn);
    animation: pulse 2.4s ease-in-out infinite;
  }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

  h1 {
    margin: 0 0 0.5rem;
    font-family: var(--display); font-weight: 800;
    font-size: clamp(2.4rem, 6vw, 3.8rem);
    line-height: 0.92; letter-spacing: 0.015em;
    text-transform: uppercase;
    text-shadow: 0 2px 26px rgba(0, 0, 0, 0.4);
  }

  .gw-kort {
    background: linear-gradient(140deg, rgba(233, 0, 82, 0.22), rgba(45, 8, 62, 0.85) 70%);
    border: 1px solid rgba(246, 242, 250, 0.2);
    border-radius: 12px;
    padding: 0.9rem 1.4rem 1rem;
    min-width: 16rem;
  }
  .gw-label {
    font-family: var(--display); font-weight: 600;
    font-size: 0.85rem; letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.35rem;
  }
  .gw-tall { font-family: var(--digits); font-weight: 700; font-size: 1.9rem; }
  .gw-meta { color: var(--muted); font-size: 0.95rem; margin-top: 0.15rem; }
  .progress {
    margin-top: 0.7rem; height: 4px;
    background: var(--divider); border-radius: 2px; overflow: hidden;
  }
  .progress > span {
    display: block; height: 100%;
    background: linear-gradient(90deg, var(--gronn), var(--cyan));
  }

  .board { display: grid; grid-template-columns: 1fr; gap: 1.25rem; align-items: start; }
  .board.to-kolonner { grid-template-columns: 1fr 1fr; }

  .col {
    background: var(--surface);
    border: 1px solid var(--divider);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 20px 44px -28px rgba(0, 0, 0, 0.9);
  }
  .col-head, .lb-row {
    display: grid;
    grid-template-columns: 4.4rem 2.2rem 1fr auto 4.2rem 5.4rem;
    align-items: center;
    gap: 0.8rem;
    padding: 0.75rem 1.3rem;
  }
  .col-head {
    font-family: var(--display); font-weight: 600;
    font-size: 0.82rem; letter-spacing: 0.2em; text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--line);
  }
  .col-head .h-rank { text-align: center; }
  .col-head .h-gw, .col-head .h-tot { text-align: right; }
  .col-head .h-tot { color: var(--gronn); }

  .lb-row { border-bottom: 1px solid var(--divider); }
  .lb-row:last-child { border-bottom: none; }

  .lb-rank {
    display: flex; align-items: baseline; justify-content: center; gap: 0.28rem;
    font-family: var(--display); font-weight: 800; font-size: 1.9rem;
    color: var(--muted); line-height: 1;
  }
  /* Bevegelse siden forrige GW. last_rank er 0 i GW1, da vises ingenting. */
  /* 1.05rem, ikke mindre: dette skal leses fra andre siden av rommet. */
  .pil {
    font-family: var(--body); font-weight: 700; font-size: 1.05rem;
    letter-spacing: -0.02em; line-height: 1;
  }
  .pil.opp { color: var(--gronn); }
  .pil.ned { color: var(--ned); }
  .pil.lik { color: var(--muted); opacity: 0.6; }
  .lb-badge { width: 2.2rem; height: 2.2rem; object-fit: contain; }
  .lb-badge.tom { opacity: 0.12; border-radius: 50%; background: var(--chalk); }

  .lb-navn { min-width: 0; }
  .lb-fornavn {
    font-weight: 700; font-size: 1.45rem; line-height: 1.15;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .lb-lagnavn {
    font-size: 1rem; color: var(--muted);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  .meta { display: flex; align-items: center; gap: 0.45rem; flex-wrap: nowrap; }
  .kaptein, .chip-badge {
    display: inline-flex; align-items: baseline; gap: 0.35rem;
    border-radius: 999px; padding: 0.18rem 0.7rem;
    font-size: 0.92rem; font-weight: 600; white-space: nowrap;
  }
  .kaptein {
    background: rgba(4, 245, 255, 0.12);
    border: 1px solid rgba(4, 245, 255, 0.32);
    color: var(--chalk);
  }
  .kaptein b { font-family: var(--digits); font-weight: 700; color: var(--cyan); font-size: 0.82em; }
  .chip-badge {
    background: rgba(246, 196, 83, 0.15);
    border: 1px solid rgba(246, 196, 83, 0.45);
    color: var(--gold);
  }

  .lb-gw, .lb-tot {
    font-family: var(--digits); font-weight: 700;
    text-align: right; font-variant-numeric: tabular-nums;
  }
  .lb-gw { font-size: 1.25rem; color: var(--muted); }
  .lb-tot {
    font-size: 1.85rem; color: var(--chalk);
    text-shadow: 0 0 20px rgba(0, 255, 135, 0.25);
  }

  .lb-row.gold   { box-shadow: inset 4px 0 0 var(--gold); }
  .lb-row.silver { box-shadow: inset 4px 0 0 var(--silver); }
  .lb-row.bronze { box-shadow: inset 4px 0 0 var(--bronze); }
  .lb-row.gold   .lb-rank { color: var(--gold); }
  .lb-row.silver .lb-rank { color: var(--silver); }
  .lb-row.bronze .lb-rank { color: var(--bronze); }

  footer {
    margin-top: 1.4rem; text-align: right;
    font-size: 0.9rem; color: var(--muted);
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 720px) {
    html { font-size: 15px; }
    .board.to-kolonner { grid-template-columns: 1fr; }
    .col-head, .lb-row { grid-template-columns: 2.2rem 1.8rem 1fr 3.2rem 4rem; gap: 0.5rem; padding: 0.6rem 0.8rem; }
    .col-head .h-meta, .meta { display: none; }
    .lb-fornavn { font-size: 1.15rem; }
    .lb-tot { font-size: 1.4rem; }
  }
"""

MEDALJE = {1: "gold", 2: "silver", 3: "bronze"}


def _pil(rank, forrige):
    """Bevegelse siden forrige GW. Tomt naar vi ikke har noe aa sammenligne med
    (GW1, eller en deltaker som nettopp har blitt med)."""
    if not forrige:
        return ""
    if rank < forrige:
        return f'<span class="pil opp">&#9650;{forrige - rank}</span>'
    if rank > forrige:
        return f'<span class="pil ned">&#9660;{rank - forrige}</span>'
    return '<span class="pil lik">&#8211;</span>'


def _rad(d):
    kls = MEDALJE.get(d["rank"], "")
    badge = (
        f'<img class="lb-badge" src="{escape(d["badge"])}" alt="">'
        if d.get("badge")
        else '<span class="lb-badge tom"></span>'
    )

    meta = []
    if d.get("chip"):
        meta.append(f'<span class="chip-badge">{escape(d["chip"])}</span>')
    if d.get("kaptein"):
        meta.append(f'<span class="kaptein"><b>C</b>{escape(d["kaptein"])}</span>')

    return f"""      <div class="lb-row {kls}">
        <div class="lb-rank">{d["rank"]}{_pil(d["rank"], d.get("forrige_rank"))}</div>
        {badge}
        <div class="lb-navn">
          <div class="lb-fornavn">{escape(d["fornavn"])}</div>
          <div class="lb-lagnavn">{escape(d["lagnavn"])}</div>
        </div>
        <div class="meta">{"".join(meta)}</div>
        <div class="lb-gw">{d["gw_poeng"]}</div>
        <div class="lb-tot">{d["total"]}</div>
      </div>"""


def _kolonne(deltakere):
    rader = "\n".join(_rad(d) for d in deltakere)
    return f"""    <div class="col">
      <div class="col-head">
        <div class="h-rank">#</div><div></div><div>Deltaker</div>
        <div class="h-meta"></div><div class="h-gw">GW</div><div class="h-tot">Tot</div>
      </div>
{rader}
    </div>"""


def render(data):
    d = data["deltakere"]
    k = data["kamper"]
    gw = data["gw"]

    if data["live"]:
        status = f'<span class="status"><span class="dot"></span>{k["live"]} kamper pågår</span>'
    elif gw["ferdig"]:
        status = f'<span class="status" style="color:var(--muted);background:none;border-color:var(--line)">{gw["navn"]} ferdig</span>'
    else:
        status = f'<span class="status" style="color:var(--muted);background:none;border-color:var(--line)">venter på avspark</span>'

    # To kolonner naar gjengen vokser forbi det en TV-hoeyde taaler i en kolonne.
    if len(d) > 12:
        midt = (len(d) + 1) // 2
        board_kls = "board to-kolonner"
        kolonner = _kolonne(d[:midt]) + "\n" + _kolonne(d[midt:])
    else:
        board_kls = "board"
        kolonner = _kolonne(d)

    pct = round(100 * k["ferdig"] / k["totalt"]) if k["totalt"] else 0
    oppdatert = (data.get("sist_oppdatert") or data["generert"]).replace("T", " ")[:16]

    return f"""<!doctype html>
<html lang="no">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="300">
<meta name="robots" content="noindex">
<title>{escape(data["liga"])}</title>
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="head-grid">
      <div>
        <div class="eyebrow"><span>Fantasy Premier League</span>{status}</div>
        <h1>{escape(data["liga"])}</h1>
      </div>
      <div class="gw-kort">
        <div class="gw-label">{escape(gw["navn"])}</div>
        <div class="gw-tall">{k["ferdig"]}<span style="color:var(--muted);font-size:0.6em"> / {k["totalt"]}</span></div>
        <div class="gw-meta">kamper ferdigspilt</div>
        <div class="progress"><span style="width:{pct}%"></span></div>
      </div>
    </div>
  </header>

  <div class="{board_kls}">
{kolonner}
  </div>

  <footer>Oppdatert {oppdatert} UTC</footer>
</div>
</body>
</html>
"""
