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
    /* Moerk og halvgjennomsiktig saa bakgrunnen leses gjennom tavla.
       0.62 er grensen der navnene fortsatt holder mot et travelt motiv -
       backdrop-filter hjelper der den stoettes, men kan ikke forutsettes. */
    --surface: rgba(9, 5, 18, 0.62);
    --surface-hover: rgba(30, 12, 48, 0.74);
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

  /* Bakgrunnsfoto. Kraftig sloering gjoer to ting: holder teksten lesbar, og
     skjuler at kilden er 686x386 og altsaa langt under TV-opploesning.
     scale(1.08) spiser vekk de gjennomsiktige kantene sloeringen lager. */
  /* Bakgrunnsfoto. Kilden er 596x335 og skaleres ~3,2x - den kan ikke bli
     skarp paa 1080p uansett hva vi gjoer. Ingen blur her, saa den i det minste
     ikke blir slørete i tillegg. scale/translate skyver den innbakte
     «PREMIER LEAGUE»-teksten i bunnen delvis ut av bildet. */
  /* Bakgrunnsfoto, 1908x1188. Ramma er satt med background-size/-position
     framfor transform fordi det er langt lettere aa regne paa:
       130% bredde  -> 2496x1554 px, altsaa bare 1,31x oppskalering
       posisjon 28% -> viser kildens rader 8,5%-78%, slik at den innbakte
                       «PREMIER LEAGUE»-teksten nederst faller utenfor.
     Ingen blur - kilden er skarp nok til aa taale full oppløsning. */
  body::before {
    content: ""; position: fixed; inset: 0; z-index: -2;
    background: url("bakgrunn.jpg") center 28% / 130% auto no-repeat;
  }
  /* Moerkleggingslag. Sterkest nederst der tavla ligger. */
  body::after {
    content: ""; position: fixed; inset: 0; z-index: -1;
    background: linear-gradient(180deg,
      rgba(8, 5, 18, 0.30) 0%,
      rgba(8, 5, 18, 0.50) 35%,
      rgba(6, 4, 14, 0.78) 100%);
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
  /* To segmenter: ferdigspilte kamper solid, paagaaende dempet og pulserende.
     Uten det andre segmentet ser stripa tom ut midt i en runde. */
  .progress {
    margin-top: 0.7rem; height: 5px; display: flex;
    background: var(--divider); border-radius: 3px; overflow: hidden;
  }
  .progress > span { display: block; height: 100%; }
  .progress .p-ferdig { background: linear-gradient(90deg, var(--gronn), var(--cyan)); }
  .progress .p-live {
    background: var(--gronn); opacity: 0.35;
    animation: pulse 2.4s ease-in-out infinite;
  }
  .gw-live {
    margin-top: 0.5rem; color: var(--gronn);
    font-size: 0.92rem; font-weight: 600;
  }

  .board { display: grid; grid-template-columns: 1fr; gap: 1.25rem; align-items: start; }
  .board.to-kolonner { grid-template-columns: 1fr 1fr; }

  .col {
    background: var(--surface);
    /* Glassplate: slipper bakgrunnen gjennom, men demper detaljene bak
       teksten saa radene holder kontrast. */
    -webkit-backdrop-filter: blur(14px) saturate(1.15);
    backdrop-filter: blur(14px) saturate(1.15);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 24px 50px -26px rgba(0, 0, 0, 0.95);
  }
  .col-head, .lb-row {
    display: grid;
    /* Foerste kolonne er bevegelsespila, helt ute til venstre og adskilt fra
       plasseringstallet. */
    grid-template-columns: 2.4rem 2.6rem 2.2rem 1fr auto 4.2rem 5.4rem 1.4rem;
    align-items: center;
    gap: 0.7rem;
    padding: 0.75rem 1.3rem 0.75rem 0.9rem;
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

  /* Rad + utfellbar detalj. <details>/<summary> gir klikk-for-aa-utvide uten
     en linje JavaScript. TV-en kan ikke klikkes uansett - dette er for telefon. */
  .lb-item { border-bottom: 1px solid var(--divider); }
  .lb-item:last-child { border-bottom: none; }
  .lb-row { cursor: pointer; list-style: none; transition: background 0.15s; }
  .lb-row::-webkit-details-marker { display: none; }
  .lb-row:hover { background: var(--surface-hover); }
  .lb-item[open] > .lb-row { background: var(--surface-hover); }

  /* Liten pil som viser at raden kan aapnes. Skjules paa TV-bredder. */
  .utvid {
    font-size: 0.9rem; color: var(--muted); opacity: 0.5;
    transition: transform 0.15s; text-align: center;
  }
  .lb-item[open] .utvid { transform: rotate(90deg); }

  .lb-rank {
    font-family: var(--display); font-weight: 800; font-size: 1.9rem;
    color: var(--muted); line-height: 1; text-align: center;
  }
  /* Bevegelse siden forrige GW - egen kolonne helt til venstre, adskilt fra
     plasseringstallet. last_rank er 0 i GW1, da staar kolonnen tom.
     1.05rem, ikke mindre: dette skal leses fra andre siden av rommet. */
  .pil {
    display: flex; align-items: center; gap: 0.08rem;
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

  /* --- utfelt detalj: bytter + banevisning --- */
  .detalj { padding: 0.4rem 1.3rem 1.3rem; background: rgba(0, 0, 0, 0.28); }

  /* Rundens poeng staar oeverst og midtstilt, med byttene under. */
  .runde-topp {
    display: flex; flex-direction: column; align-items: center;
    padding: 0.7rem 0 0.9rem;
    border-bottom: 1px solid var(--divider);
    margin-bottom: 0.9rem;
  }
  .bytter {
    display: flex; align-items: center; justify-content: center;
    gap: 0.9rem; flex-wrap: wrap;
    margin-top: 0.55rem;
  }
  .bytter-tittel {
    font-family: var(--display); font-weight: 600;
    font-size: 0.85rem; letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--muted);
  }
  .bytter-tom { color: var(--muted); opacity: 0.65; font-size: 0.98rem; }
  .bytte { display: inline-flex; align-items: center; gap: 0.5rem; font-size: 1.02rem; }
  .bytte .ut { color: var(--ned); font-weight: 700; }
  .bytte .inn { color: var(--gronn); font-weight: 700; }
  .bytte .pil-ut, .bytte .pil-inn { font-weight: 800; letter-spacing: -0.08em; }
  .bytte .pil-ut { color: var(--ned); }
  .bytte .pil-inn { color: var(--gronn); }
  .gw-poeng-stor {
    font-family: var(--digits); font-weight: 700; font-size: 1.9rem;
    line-height: 1; text-align: center;
  }
  .gw-poeng-stor span {
    display: block;
    font-family: var(--display); font-size: 0.42em; font-weight: 600;
    letter-spacing: 0.22em; text-transform: uppercase; color: var(--muted);
    margin-bottom: 0.25rem;
  }

  /* Banen. Griden er fire rader (K/F/M/A) og benken ligger som egen stripe. */
  .bane {
    background:
      linear-gradient(180deg, rgba(0, 92, 47, 0.55), rgba(0, 58, 30, 0.72)),
      repeating-linear-gradient(180deg, rgba(255,255,255,0.045) 0 2.6rem, transparent 2.6rem 5.2rem);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 1rem 0.6rem 0.9rem;
    display: grid; gap: 0.7rem;
  }
  .bane-rad { display: flex; justify-content: center; gap: 1.15rem; flex-wrap: wrap; }

  .benk {
    margin-top: 0.7rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--divider);
    border-radius: 10px;
    padding: 0.7rem 0.6rem;
  }
  .benk-tittel {
    font-family: var(--display); font-weight: 600;
    font-size: 0.8rem; letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--muted); text-align: center; margin-bottom: 0.5rem;
  }

  .spiller { width: 5.4rem; text-align: center; position: relative; }
  .spiller img { width: 3.1rem; height: 3.1rem; object-fit: contain; display: block; margin: 0 auto; }
  .spiller-navn {
    font-size: 0.86rem; font-weight: 600;
    background: rgba(0, 0, 0, 0.55); border-radius: 3px 3px 0 0;
    padding: 0.1rem 0.2rem; margin-top: 0.2rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .spiller-poeng {
    font-family: var(--digits); font-weight: 700; font-size: 0.92rem;
    background: var(--gronn); color: #06231a;
    border-radius: 0 0 3px 3px; padding: 0.06rem 0.2rem;
  }
  .benk .spiller-poeng { background: var(--muted); color: #241033; }
  .spiller-poeng.ikke-spilt { background: rgba(255, 255, 255, 0.22); color: var(--chalk); }
  .kaptein-merke {
    position: absolute; top: -0.15rem; right: 0.55rem;
    width: 1.25rem; height: 1.25rem; border-radius: 50%;
    background: var(--chalk); color: #240132;
    font-family: var(--digits); font-weight: 700; font-size: 0.72rem;
    display: flex; align-items: center; justify-content: center;
  }
  .kaptein-merke.vise { background: var(--muted); }

  footer {
    margin-top: 1.4rem; text-align: right;
    font-size: 0.9rem; color: var(--muted);
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 720px) {
    html { font-size: 15px; }
    .board.to-kolonner { grid-template-columns: 1fr; }
    .col-head, .lb-row {
      grid-template-columns: 3.4rem 1.8rem 1fr 3.2rem 4rem 1.2rem;
      gap: 0.5rem; padding: 0.6rem 0.7rem;
    }
    /* Kaptein/chip-pillene tar for mye bredde paa telefon - de staar
       uansett i detaljvisningen som er hovedpoenget der. */
    .col-head .h-meta, .meta { display: none; }
    .lb-fornavn { font-size: 1.15rem; }
    .lb-tot { font-size: 1.4rem; }
    .detalj { padding: 0.4rem 0.6rem 1rem; }
    .spiller { width: 4.4rem; }
    .spiller img { width: 2.5rem; height: 2.5rem; }
    .gw-poeng-stor { margin-left: 0; }
  }
"""

MEDALJE = {1: "gold", 2: "silver", 3: "bronze"}


def _pil(rank, forrige):
    """Bevegelse siden forrige GW, som egen celle helt til venstre. Tom naar vi
    ikke har noe aa sammenligne med (GW1, eller en nyinnmeldt deltaker)."""
    if not forrige:
        return '<div class="pil"></div>'
    if rank < forrige:
        return f'<div class="pil opp">&#9650;{forrige - rank}</div>'
    if rank > forrige:
        return f'<div class="pil ned">&#9660;{rank - forrige}</div>'
    return '<div class="pil lik">&#8211;</div>'


SHIRT = "https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_{kode}{gk}-110.png"


def _spiller(sp):
    """En drakt med navn og poeng. Keepere har egen draktvariant (_1)."""
    merke = ""
    if sp["kaptein"]:
        merke = '<span class="kaptein-merke">C</span>'
    elif sp["vise"]:
        merke = '<span class="kaptein-merke vise">V</span>'
    url = SHIRT.format(kode=sp["lag_kode"], gk="_1" if sp["type"] == 1 else "")
    # Strek naar spilleren ikke har vaert paa banen enda. «0» er forbeholdt
    # dem som faktisk spilte og ikke fikk poeng.
    poeng = sp["poeng"] if sp.get("spilt") else "&ndash;"
    ikke_spilt = "" if sp.get("spilt") else " ikke-spilt"
    return (
        f'<div class="spiller">{merke}'
        f'<img src="{url}" alt="" loading="lazy">'
        f'<div class="spiller-navn">{escape(sp["navn"])}</div>'
        f'<div class="spiller-poeng{ikke_spilt}">{poeng}</div>'
        f"</div>"
    )


def _bane(tropp):
    """Startellever gruppert K/F/M/A, benken i egen stripe under."""
    if not tropp:
        return '<div class="bytter-tom">Laget er ikke synlig før deadline.</div>'

    start = sorted((s for s in tropp if s["posisjon"] <= 11), key=lambda s: s["posisjon"])
    benk = sorted((s for s in tropp if s["posisjon"] > 11), key=lambda s: s["posisjon"])

    rader = []
    for t in (1, 2, 3, 4):
        i_rad = [s for s in start if s["type"] == t]
        if i_rad:
            rader.append(f'<div class="bane-rad">{"".join(_spiller(s) for s in i_rad)}</div>')

    benk_html = ""
    if benk:
        benk_html = (
            '<div class="benk"><div class="benk-tittel">Benk</div>'
            f'<div class="bane-rad">{"".join(_spiller(s) for s in benk)}</div></div>'
        )
    return f'<div class="bane">{"".join(rader)}</div>{benk_html}'


def _bytter(d):
    """Rundens poeng oeverst og midtstilt, byttene under.

    Byttestripa staar tom til transfers-endepunktet er verifisert mot ekte
    data - foerste sjanse er GW2-deadline."""
    if d.get("bytter"):
        biter = "".join(
            f'<span class="bytte"><span class="pil-ut">&laquo;&laquo;&laquo;</span>'
            f'<span class="ut">{escape(b["ut"])}</span>'
            f'<span class="pil-inn">&raquo;&raquo;&raquo;</span>'
            f'<span class="inn">{escape(b["inn"])}</span></span>'
            for b in d["bytter"]
        )
    else:
        biter = '<span class="bytter-tom">Ingen bytter denne runden</span>'

    trekk = f' <span class="ut">(&minus;{d["trekk"]})</span>' if d.get("trekk") else ""
    return (
        f'<div class="runde-topp">'
        f'<div class="gw-poeng-stor"><span>Rundens poeng</span>{d["gw_poeng"]}{trekk}</div>'
        f'<div class="bytter"><span class="bytter-tittel">Bytter</span>{biter}</div>'
        f"</div>"
    )


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

    return f"""      <details class="lb-item">
        <summary class="lb-row {kls}">
          {_pil(d["rank"], d.get("forrige_rank"))}
          <div class="lb-rank">{d["rank"]}</div>
          {badge}
          <div class="lb-navn">
            <div class="lb-fornavn">{escape(d["fornavn"])}</div>
            <div class="lb-lagnavn">{escape(d["lagnavn"])}</div>
          </div>
          <div class="meta">{"".join(meta)}</div>
          <div class="lb-gw">{d["gw_poeng"]}</div>
          <div class="lb-tot">{d["total"]}</div>
          <div class="utvid">&#9656;</div>
        </summary>
        <div class="detalj">
{_bytter(d)}
{_bane(d.get("tropp") or [])}
        </div>
      </details>"""


def _kolonne(deltakere):
    rader = "\n".join(_rad(d) for d in deltakere)
    return f"""    <div class="col">
      <div class="col-head">
        <div></div><div class="h-rank">#</div><div></div><div>Deltaker</div>
        <div class="h-meta"></div><div class="h-gw">GW</div><div class="h-tot">Tot</div><div></div>
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
    pct_live = round(100 * k["live"] / k["totalt"]) if k["totalt"] else 0
    live_linje = f'<div class="gw-live">{k["live"]} pågår nå</div>' if k["live"] else ""
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
        <div class="progress">
          <span class="p-ferdig" style="width:{pct}%"></span>
          <span class="p-live" style="width:{pct_live}%"></span>
        </div>
        {live_linje}
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
