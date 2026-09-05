"""HTML-generator for FPL-tavla.

Samme strukturelle grep som VM-tavla (flytende vh-skalering for TV, kortbasert
ledertavle, gull/soelv/bronse paa topp tre), men Premier League-paletten i stedet
for den roede VM-bakgrunnen.
"""

from datetime import datetime, timedelta, timezone
from html import escape

try:
    from zoneinfo import ZoneInfo

    OSLO = ZoneInfo("Europe/Oslo")
except Exception:  # tzdata mangler - fall tilbake paa fast sommertid
    OSLO = timezone(timedelta(hours=2))


def _norsk_tid(iso):
    """UTC-tidsstempel fra API-et om til norsk lokaltid."""
    if not iso:
        return ""
    t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(OSLO).strftime("%d.%m kl. %H:%M")

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

  /* Bakgrunnsfoto: Old Trafford, kilde 4256x2756 nedskalert til 2560x1658.
     120% bredde gir 2304 px paa en 1920-skjerm, altsaa fortsatt nedskalering
     og full skarphet. Posisjon 22% biaser mot tribunene og flomlyset oeverst
     og tar med omtrent halve banen. */
  body::before {
    content: ""; position: fixed; inset: 0; z-index: -2;
    background: url("bakgrunn.jpg") center 22% / 120% auto no-repeat;
  }
  /* Moerkleggingslag. Denne bakgrunnen er motsatt av den forrige - lys
     graesmatte nederst, moerk himmel oeverst - saa dempingen maa vaere
     kraftigst i bunnen for at radene skal holde kontrast. */
  body::after {
    content: ""; position: fixed; inset: 0; z-index: -1;
    background: linear-gradient(180deg,
      rgba(6, 4, 14, 0.42) 0%,
      rgba(6, 4, 14, 0.58) 30%,
      rgba(5, 3, 12, 0.86) 100%);
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

  /* Tegnforklaring under tittelen. Ligger i lufta som allerede fantes mellom
     h1 og bunnen av GW-kortet, saa headeren ikke blir hoeyere og tavla ikke
     skyves nedover. */
  .tegnforklaring {
    display: flex; align-items: center; gap: 1.4rem; flex-wrap: wrap;
    margin-top: 0.15rem;
    font-size: 0.86rem;
    /* Gull brukes ellers bare til foersteplassen, saa fargen er ledig her og
       skiller forklaringen fra selve tavla. */
    color: var(--gold);
  }
  .tf { display: inline-flex; align-items: center; gap: 0.42rem; }
  .tf-ring.verst { border-color: transparent; outline: 2px solid var(--ned); outline-offset: 1px; }
  .tf-ring {
    width: 1.5rem; height: 1.5rem; border-radius: 50%;
    border: 2px solid var(--gronn);
    display: flex; align-items: center; justify-content: center;
    font-family: var(--display); font-weight: 800; font-size: 0.95rem;
    color: var(--chalk); line-height: 1;
  }
  .tf .brukt-chip, .tf .chip-badge { font-size: 0.72rem; padding: 0.08rem 0.32rem; }
  .tf .chip-badge { border-radius: 4px; }

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

  /* Med to kolonner har hver rad bare halve bredden. De faste kolonnene
     summerer til ~60rem og sprenger da tavla - GW og Tot ble kuttet bort.
     Klubblogo, aktiv chip og kaptein vikes; alle tre staar i utfellingen.
     Navnekolonnen krympes, men chip-slissene beholdes fordi de er det eneste
     som skiller radene visuelt. */
  .to-kolonner .col-head,
  .to-kolonner .lb-row {
    /* Navnet er minmax(0,1fr) og ikke fast: da suger det opp slakken og
       kuttes med ellipse i stedet for at raden flyter over og spiser
       Tot-kolonnen. Slissene er pil, plassering, navn, chips, GW, Tot, pil.
       Fyllkolonnen mellom chips og GW settes til 0 her. */
    grid-template-columns: 2.2rem 2.4rem minmax(0, 1fr) auto 0 4rem 5rem 1.3rem;
    gap: 0.45rem;
    padding: 0.7rem 0.8rem;
  }
  .to-kolonner .brukt-chips { grid-template-columns: repeat(4, 1.9rem); }
  .to-kolonner .lb-badge,
  .to-kolonner .meta-chip,
  .to-kolonner .meta-kaptein { display: none; }
  .to-kolonner .lb-lagnavn { font-size: 1.25rem; }
  .to-kolonner .lb-rank { font-size: 1.7rem; }
  .to-kolonner .lb-tot { font-size: 1.6rem; }

  .col {
    background: var(--surface);
    /* Glassplate: slipper bakgrunnen gjennom, men demper detaljene bak
       teksten saa radene holder kontrast. */
    -webkit-backdrop-filter: blur(14px) saturate(1.15);
    backdrop-filter: blur(14px) saturate(1.15);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 12px;
    /* Ikke overflow:hidden - premiene skal kunne stikke ut i margen.
       Radene runder derfor av hjoernene sine selv. */
    box-shadow: 0 24px 50px -26px rgba(0, 0, 0, 0.95);
  }
  .col-head, .lb-row {
    display: grid;
    /* Foerste kolonne er bevegelsespila, helt ute til venstre og adskilt fra
       plasseringstallet. */
    /* Alt som skal flukte loddrett har fast bredde, ikke auto:
         15rem   lagnavn - rommer «Hans Magnus's Team»
         8.6rem  aktiv chip - rommer «Triple Captain», det lengste chipnavnet
         11rem   kaptein - rommer 16 tegn, som er det lengste web_name i
                 hele Premier League («Borges Rodrigues»)
       Innholdet i de to siste sentreres i slissen sin. 1fr-slissen mellom
       chipsene og hoeyre halvdel tar opp resten. */
    grid-template-columns: 2.4rem 2.6rem 2.2rem 15rem auto 1fr 8.6rem 11rem 4.2rem 5.4rem 1.4rem;
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
  .lb-item:last-child { border-bottom: none; overflow: hidden; border-radius: 0 0 12px 12px; }
  .lb-row { position: relative; cursor: pointer; list-style: none; transition: background 0.15s; }

  /* Premier ligger i margen til venstre for kortet, utenfor medaljestripa.
     Pengene er ikke tabelldata - de er en belaanning, og faar sitt eget felt.
     Fargen matcher markoeren premien hoerer til: gull- og soelvstripe for
     plassering, groenn ring for beste enkeltrunde. Da ser man med én gang
     hvorfor noen faar penger. Stables naar samme person vinner flere. */
  .premier {
    position: absolute; right: 100%; top: 50%;
    transform: translateY(-50%);
    margin-right: 1.1rem;
    display: flex; flex-direction: column; align-items: flex-end; gap: 0.25rem;
  }
  .premie {
    font-family: var(--digits); font-weight: 700; font-size: 0.95rem;
    white-space: nowrap; border-radius: 999px;
    padding: 0.2rem 0.75rem; border: 1px solid;
  }
  .premie.gold   { color: var(--gold);   border-color: rgba(246, 196, 83, 0.5);  background: rgba(246, 196, 83, 0.13); }
  .premie.silver { color: var(--silver); border-color: rgba(220, 214, 226, 0.45); background: rgba(220, 214, 226, 0.12); }
  .premie.bronze { color: var(--bronze); border-color: rgba(224, 160, 112, 0.5); background: rgba(224, 160, 112, 0.13); }
  .premie.beste  { color: var(--gronn);  border-color: rgba(0, 255, 135, 0.45);  background: rgba(0, 255, 135, 0.12); }
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

  /* Lagnavnet er det folk kjenner hverandre paa - det staar stort,
     fornavnet under i det smaa. */
  .lb-navn { min-width: 0; }
  .lb-lagnavn {
    font-weight: 700; font-size: 1.45rem; line-height: 1.15;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .lb-fornavn {
    font-size: 1rem; color: var(--muted);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  /* Hver sin faste slisse, innholdet sentrert i den. */
  .meta-chip, .meta-kaptein {
    display: flex; align-items: center; justify-content: center;
    min-width: 0;
  }
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
    background: rgba(0, 255, 135, 0.14);
    border: 1px solid rgba(0, 255, 135, 0.45);
    color: var(--gronn);
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

  /* Beste enkeltrunde - tredje premie. Groenn ring rundt plasseringstallet,
     ikke enda en boks. Tallet beholder medaljefargen sin inni ringen, saa
     1./2. plass og beste GW kan vises samtidig uten aa slaas om plassen. */
  .lb-rank.beste, .lb-rank.verst {
    border-radius: 50%;
    width: 2.5rem; height: 2.5rem;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto;
  }
  .lb-rank.beste {
    border: 2px solid var(--gronn);
    box-shadow: 0 0 12px -2px rgba(0, 255, 135, 0.55);
  }
  /* Verste enkeltrunde. outline i stedet for border, saa ringen legger seg
     UTENFOR den groenne og begge synes naar samme person eier begge. */
  .lb-rank.verst {
    outline: 2px solid var(--ned);
    outline-offset: 3px;
  }

  /* Oppbrukte chips: forkortelse i roed boks, tett inntil navnet.
     Fast rutenett med én kolonne per chip-type (BB, TC, WC, FH) slik at de
     staar loddrett over hverandre paa tvers av radene - mangler noen en chip
     blir slissen staaende tom i stedet for at de andre glir mot venstre. */
  .brukt-chips {
    display: grid;
    grid-template-columns: repeat(4, 2.2rem);
    gap: 0.25rem;
  }
  .brukt-chips > span { justify-self: start; }
  .brukt-chip {
    font-family: var(--digits); font-weight: 700; font-size: 0.78rem;
    color: var(--ned); background: rgba(255, 77, 77, 0.13);
    border: 1px solid rgba(255, 77, 77, 0.42);
    border-radius: 4px; padding: 0.12rem 0.35rem;
  }

  /* Naar deltakerens beste og verste runde skjedde. Ligger i 1fr-kolonnen
     som ellers stod tom mellom chipsene og aktiv-chip-slissen. */
  .ring-info {
    display: flex; flex-direction: column; align-items: flex-end;
    gap: 0.25rem; line-height: 1.2;
    font-size: 0.92rem; color: var(--muted);
  }
  .ri { display: inline-flex; align-items: center; gap: 0.35rem; white-space: nowrap; }
  .ri-ring {
    width: 0.85rem; height: 0.85rem; border-radius: 50%;
    flex: none; box-sizing: border-box;
  }
  .ri-ring.beste { border: 2px solid var(--gronn); }
  .ri-ring.verst { border: 2px solid var(--ned); }

  /* --- GW-navigasjon i utfellingen --- */
  /* Navigasjon og poeng deler midtkolonnen, saa «Bytter» og rundeinfoen
     kan ligge i hvert sitt oevre hjoerne i stedet for aa ta egne linjer. */
  .runde-midt { display: flex; flex-direction: column; align-items: center; gap: 0.35rem; }
  .gw-nav {
    display: flex; align-items: center; justify-content: center;
    gap: 0.9rem;
  }
  .gw-pil {
    background: rgba(4, 245, 255, 0.1);
    border: 1px solid rgba(4, 245, 255, 0.35);
    color: var(--cyan); cursor: pointer;
    border-radius: 6px; padding: 0.1rem 0.6rem;
    font-size: 0.9rem; line-height: 1.5;
    font-family: var(--body);
    transition: background 0.15s;
  }
  .gw-pil:hover { background: rgba(4, 245, 255, 0.22); }
  .gw-pil.av {
    background: none; border-color: var(--divider);
    color: var(--muted); opacity: 0.3; cursor: default;
    border-radius: 6px; padding: 0.1rem 0.6rem; font-size: 0.9rem;
    border-width: 1px; border-style: solid;
  }
  .gw-merke {
    font-family: var(--display); font-weight: 600;
    font-size: 0.85rem; letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--muted); min-width: 9rem; text-align: center;
  }
  .detalj.laster { opacity: 0.45; }

  /* --- utfelt detalj: bytter + banevisning --- */
  .detalj { padding: 0.4rem 1.3rem 1.3rem; background: rgba(0, 0, 0, 0.28); }

  /* Tre kolonner: byttene oppe til venstre, rundens poeng midtstilt.
     Hoeyre kolonne staar tom og finnes bare for aa holde midten i midten. */
  .runde-topp {
    display: grid; grid-template-columns: 1fr auto 1fr; align-items: start;
    gap: 1rem;
    padding: 0.7rem 0 0.9rem;
    border-bottom: 1px solid var(--divider);
    margin-bottom: 0.9rem;
  }
  .bytter-tittel {
    display: block;
    font-family: var(--display); font-weight: 600;
    font-size: 0.85rem; letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.4rem;
  }
  .bytter-tom { color: var(--muted); opacity: 0.65; font-size: 0.98rem; }
  /* Ut og inn i hver sin loddrette bolk. Lista vokser nedover og skyver banen
     ned med seg - .detalj er en vanlig blokk, saa de kan ikke overlappe. */
  .bytte-liste { display: grid; gap: 0.12rem; }
  .bytte-rad {
    display: flex; align-items: baseline; gap: 0.5rem;
    font-size: 1.02rem; white-space: nowrap;
  }
  .bytte-rad .ut { color: var(--ned); font-weight: 700; }
  .bytte-rad .inn { color: var(--gronn); font-weight: 700; }
  .pil-ut, .pil-inn { font-weight: 800; letter-spacing: -0.08em; }
  .pil-ut { color: var(--ned); }
  .pil-inn { color: var(--gronn); }
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
      linear-gradient(180deg, rgba(0, 86, 44, 0.93), rgba(0, 52, 27, 0.96)),
      repeating-linear-gradient(180deg, rgba(255,255,255,0.045) 0 2.6rem, transparent 2.6rem 5.2rem);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 1.4rem 0.6rem 1.2rem;
    display: grid; gap: 1.1rem;
  }
  .bane-rad { display: flex; justify-content: center; gap: 1.3rem; flex-wrap: wrap; }

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

  .spiller { width: 6.8rem; text-align: center; position: relative; }
  .spiller img { width: 3.9rem; height: 3.9rem; object-fit: contain; display: block; margin: 0 auto; }
  .spiller-navn {
    font-size: 0.95rem; font-weight: 600;
    background: rgba(0, 0, 0, 0.55); border-radius: 3px 3px 0 0;
    padding: 0.1rem 0.2rem; margin-top: 0.2rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .spiller-poeng {
    font-family: var(--digits); font-weight: 700; font-size: 1.02rem;
    background: var(--gronn); color: #06231a;
    border-radius: 0 0 3px 3px; padding: 0.06rem 0.2rem;
  }
  .benk .spiller-poeng { background: var(--muted); color: #241033; }
  .spiller-poeng.ikke-spilt { background: rgba(255, 255, 255, 0.22); color: var(--chalk); }
  /* Motstander i stedet for poeng naar kampen ikke har startet. Krymper litt,
     siden «AVL (A)» er bredere enn et tosifret tall. */
  .spiller-poeng.kamp {
    font-family: var(--body); font-weight: 600;
    font-size: 0.74rem; letter-spacing: -0.01em;
  }
  /* Dobbeltrunde: kampene side om side med skillestrek, foerste kamp foerst. */
  .spiller-poeng.dobbel {
    display: flex; align-items: center; justify-content: center; gap: 0.3rem;
    font-size: 0.62rem; padding: 0.1rem 0.15rem;
  }
  .spiller-poeng.dobbel > span + span {
    border-left: 1px solid rgba(36, 16, 51, 0.45); padding-left: 0.3rem;
  }
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

  /* Aktiv chip: fullt navn paa TV, forkortelse paa mobil. */
  .chip-badge .kort { display: none; }

  /* Andre-linje-beholderen for mobil. display:contents gjoer den usynlig for
     TV-gridet - barna er fortsatt direkte grid-items og layouten er uendret. */
  .mobil-linje { display: contents; }

  /* ------------------------------------------------------------------
     MOBIL. Alt herfra gjelder kun under 720 px og roerer ikke TV-visningen.
     Raden gaar fra 11 kolonner til et 2x4-rutenett:
        rad 1:  plassering | lagnavn + fornavn | GW | Tot
        rad 2:              | chips + aktiv chip + kaptein
     ------------------------------------------------------------------ */
  @media (max-width: 720px) {
    html { font-size: 13px; }
    .wrap { padding: 0.9rem 0.7rem 1rem; }
    .board.to-kolonner { grid-template-columns: 1fr; }

    /* --- header --- */
    header { margin-bottom: 0.7rem; }
    .head-grid { flex-direction: column; align-items: stretch; gap: 0.7rem; }
    h1 { font-size: 1.85rem; line-height: 1; }
    .eyebrow { font-size: 0.8rem; letter-spacing: 0.2em; gap: 0.6rem; margin-bottom: 0.3rem; }
    .tegnforklaring { gap: 0.5rem 0.9rem; font-size: 0.76rem; }
    .tf-ring { width: 1.25rem; height: 1.25rem; font-size: 0.8rem; }
    /* GW-kortet blir en flat stripe i stedet for et hoeyt kort. */
    .gw-kort {
      min-width: 0; padding: 0.5rem 0.8rem;
      display: grid; grid-template-columns: 1fr auto; align-items: center;
      gap: 0.2rem 0.8rem;
    }
    .gw-label { margin-bottom: 0; font-size: 0.76rem; }
    .gw-tall { font-size: 1.3rem; text-align: right; grid-row: 1 / 3; grid-column: 2; }
    .gw-meta { font-size: 0.78rem; }
    .progress { grid-column: 1 / 3; margin-top: 0.35rem; height: 3px; }
    .gw-live { grid-column: 1 / 3; margin-top: 0.3rem; font-size: 0.8rem; }

    /* --- radene --- */
    .col-head { display: none; }
    .col-head, .lb-row {
      grid-template-columns: 2.2rem 1fr auto 2.4rem 3.2rem;
      gap: 0.2rem 0.45rem;
      padding: 0.5rem 0.6rem;
    }
    /* Bilder og fyllkolonner ut - klubblogoene er tomme for de fleste
       uansett, og pila stjeler bredde vi ikke har. */
    /* Premiene er en TV-greie - det finnes ingen marg aa henge dem i her. */
    .lb-badge, .spacer, .utvid, .pil, .premier { display: none; }

    .lb-rank { grid-column: 1; grid-row: 1 / 3; font-size: 1.5rem; align-self: center; }
    .lb-rank.beste, .lb-rank.verst { width: 1.9rem; height: 1.9rem; }
    .lb-rank.verst { outline-offset: 2px; }
    .lb-navn { grid-column: 2; grid-row: 1; }
    .lb-lagnavn { font-size: 1.05rem; }
    .lb-fornavn { font-size: 0.8rem; }
    /* Kapteinen hoeyrerettet paa navnelinja, foer poengene. */
    .meta-kaptein {
      grid-column: 3; grid-row: 1;
      justify-content: flex-end; align-self: center; min-width: 0;
    }
    .lb-gw  { grid-column: 4; grid-row: 1; font-size: 0.95rem; align-self: center; }
    .lb-tot { grid-column: 5; grid-row: 1; font-size: 1.25rem; align-self: center; }

    /* Andre linje: chips og kaptein. Fast justering er en TV-luksus vi ikke
       har raad til her, saa slissene faar flyte. */
    /* Andre linje under navnet: fem faste slisser i rekkefoelgen
       [BB] [TC] [WC] [FH] [aktiv]. display:contents paa .brukt-chips loefter
       de fire slissene opp som celler i denne raden, saa de flukter loddrett
       mellom radene akkurat som paa TV. Tomme slisser staar tomme. */
    .mobil-linje {
      grid-column: 2 / -1; grid-row: 2;
      display: grid;
      grid-template-columns: repeat(4, 1.8rem) auto;
      gap: 0.22rem;
      justify-content: start; align-items: center;
    }
    .mobil-linje .spacer { display: none; }
    .brukt-chips { display: contents; }
    .brukt-chips > span { justify-self: start; }
    .brukt-chip { font-size: 0.68rem; padding: 0.05rem 0.28rem; }
    /* Chipsene ligger paa egen linje under navnet, og kaptein og poeng staar
       paa linja over - saa det er rikelig plass mot hoeyre. Aktiv chip beholder
       derfor fullt navn. Bare de oppbrukte forkortes, de staar i faste slisser. */
    .meta-chip { justify-content: flex-start; min-width: 0; }
    .chip-badge, .kaptein { font-size: 0.72rem; padding: 0.05rem 0.4rem; }

    /* --- detaljvisning --- */
    .detalj { padding: 0.3rem 0.4rem 0.8rem; }
    /* Bytter til venstre, rundens poeng til hoeyre. Stablet over hverandre
       ble navnene trange; side om side faar de hele bredden minus poengene.
       Den tomme tredje cellen som midtstiller poengene paa TV er unoedvendig
       her og skjules, ellers ville den lagt igjen en tom rad. */
    .runde-topp {
      grid-template-columns: 1fr auto;
      gap: 0.4rem 0.9rem;
      justify-items: stretch; align-items: start;
    }
    /* Tre rader: pilene sentrert oeverst over hele bredden, deretter bytter
       til venstre og poengblokka til hoeyre. display:contents paa .runde-midt
       loeser opp TV-grupperingen saa nav og poeng kan plasseres hver for seg. */
    .runde-topp {
      grid-template-columns: 1fr auto;
      gap: 0.15rem 0.8rem;
      align-items: start;
    }
    .runde-midt { display: contents; }
    .gw-nav {
      grid-column: 1 / -1; grid-row: 1;
      justify-content: center; gap: 0.6rem;
      margin-bottom: 0.55rem;
    }
    /* 9rem er satt for TV; her presser den pilene fra hverandre. */
    .gw-merke { min-width: 0; font-size: 0.78rem; letter-spacing: 0.18em; }
    .bytter { grid-column: 1; grid-row: 2 / 4; }
    .gw-poeng-stor {
      grid-column: 2; grid-row: 2;
      font-size: 1.4rem; text-align: right;
    }
    .ring-info {
      grid-column: 2; grid-row: 3;
      align-items: flex-end; font-size: 0.8rem; gap: 0.2rem;
      margin-top: 0.3rem;
    }
    .ri-ring { width: 0.75rem; height: 0.75rem; }
    /* Fire spillere paa rad maa faa plass paa 390 px:
       4 x 3.5rem + 3 x 0.4rem = 15,2rem ~ 198 px. */
    /* Bredden er det vi har rikelig av paa mobil; hoeyden gaar det ogsaa an
       aa bruke litt mer av. 4 x 4.6rem + 3 x 0.5rem = 19,9rem ~ 259 px av
       de ~360 tilgjengelige, saa det er luft igjen til dobbeltrunder. */
    .bane { padding: 0.75rem 0.25rem 0.65rem; gap: 0.6rem; }
    .bane-rad { gap: 0.35rem; }
    .spiller { width: 5.2rem; }
    .spiller img { width: 2.7rem; height: 2.7rem; }
    .spiller-navn { font-size: 0.76rem; }
    .spiller-poeng { font-size: 0.84rem; }
    .spiller-poeng.kamp { font-size: 0.7rem; }
    .spiller-poeng.dobbel { font-size: 0.54rem; gap: 0.2rem; }
    .spiller-poeng.dobbel > span + span { padding-left: 0.2rem; }
    .kaptein-merke { width: 1.15rem; height: 1.15rem; font-size: 0.66rem; right: 0.5rem; }
    .benk { padding: 0.7rem 0.3rem; }
    .kaptein-merke { width: 0.95rem; height: 0.95rem; font-size: 0.58rem; right: 0.25rem; }
    .benk { margin-top: 0.5rem; padding: 0.5rem 0.3rem; }

    footer { font-size: 0.76rem; }
  }
"""

# Fast rekkefoelge paa chip-slissene, saa kolonnene flukter mellom radene.
CHIP_REKKEFOLGE = ("BB", "TC", "WC", "FH")


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
    # Har spilleren vaert paa banen viser vi poengene. Har kampen hans ikke
    # startet enda, viser vi motstanderen i stedet. Strek er forbeholdt dem
    # hvis kamp er i gang eller ferdig uten at de kom paa.
    if sp.get("spilt"):
        poeng, ikke_spilt = sp["poeng"], ""
    elif sp.get("motstander"):
        kamper = sp["motstander"]
        if isinstance(kamper, str):          # eldre bufrede runder
            kamper = [kamper]
        poeng = "".join(f"<span>{escape(k)}</span>" for k in kamper)
        ikke_spilt = " ikke-spilt kamp" + (" dobbel" if len(kamper) > 1 else "")
    else:
        poeng, ikke_spilt = "&ndash;", " ikke-spilt"
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


def _bytter(d, nav=""):
    """Rundens poeng midtstilt, byttene oppe til venstre.

    Ut og inn staar i hver sin loddrette bolk - alle roede foerst, saa alle
    groenne. Med Free Hit eller Wildcard er antallet bytter ubegrenset, og da
    slaas lista av framfor aa la den vokse ukontrollert.
    """
    aktiv = d.get("chip")
    if aktiv in ("Free Hit", "Wildcard"):
        liste = f'<div class="bytter-tom">{escape(aktiv)} aktiv &ndash; bytter vises ikke</div>'
    elif d.get("bytter"):
        rader = [
            f'<div class="bytte-rad"><span class="pil-ut">&laquo;&laquo;&laquo;</span>'
            f'<span class="ut">{escape(b["ut"])}</span></div>'
            for b in d["bytter"]
        ] + [
            f'<div class="bytte-rad"><span class="pil-inn">&raquo;&raquo;&raquo;</span>'
            f'<span class="inn">{escape(b["inn"])}</span></div>'
            for b in d["bytter"]
        ]
        liste = f'<div class="bytte-liste">{"".join(rader)}</div>'
    else:
        liste = '<div class="bytter-tom">Ingen bytter denne runden</div>'

    trekk = f' <span class="ut">(&minus;{d["trekk"]})</span>' if d.get("trekk") else ""

    # Naar runden skjedde - bare for dem som eier en ring. Samme symboler som
    # tegnforklaringen, saa de betyr det samme overalt.
    ringer = ""
    if d.get("har_beste_gw") and d.get("beste_gw_nr"):
        ringer += (f'<span class="ri"><span class="ri-ring beste"></span>'
                   f'&ndash; GW{d["beste_gw_nr"]}</span>')
    if d.get("har_verste_gw") and d.get("verste_gw_nr"):
        ringer += (f'<span class="ri"><span class="ri-ring verst"></span>'
                   f'&ndash; GW{d["verste_gw_nr"]}</span>')

    return (
        f'<div class="runde-topp">'
        f'<div class="bytter"><span class="bytter-tittel">Bytter</span>{liste}</div>'
        f'<div class="runde-midt">{nav}'
        f'<div class="gw-poeng-stor"><span>Rundens poeng</span>{d["gw_poeng"]}{trekk}</div></div>'
        f'<div class="ring-info">{ringer}</div>'
        f"</div>"
    )


def _gw_nav(d, gw_na, gw_liste):
    """Piler for aa bla mellom gameweeks. Utelates hvis vi bare har én runde."""
    if not gw_liste or len(gw_liste) < 2:
        return ""
    i = gw_liste.index(gw_na) if gw_na in gw_liste else len(gw_liste) - 1
    forrige = gw_liste[i - 1] if i > 0 else None
    neste = gw_liste[i + 1] if i < len(gw_liste) - 1 else None

    def knapp(gw, tegn, klasse):
        if gw is None:
            return f'<span class="gw-pil av">{tegn}</span>'
        return f'<button class="gw-pil {klasse}" data-gw="{gw}" type="button">{tegn}</button>'

    return (
        f'<div class="gw-nav" data-entry="{d["entry"]}" data-gw="{gw_na}">'
        f'{knapp(forrige, "&#9664;", "bak")}'
        f'<span class="gw-merke">Gameweek {gw_na}</span>'
        f'{knapp(neste, "&#9654;", "fram")}'
        f"</div>"
    )


def detalj(d, gw_na=None, gw_liste=None):
    """Innholdet i utfellingen: navigasjon, bytter og banevisning.

    Brukes baade naar sida bygges og naar build.py forhaandsrendrer de
    historiske rundene til dist/lag/, saa markupen aldri kan komme i utakt.
    """
    return (
        f'{_bytter(d, _gw_nav(d, gw_na, gw_liste))}'
        f'{_bane(d.get("tropp") or [])}'
    )


def _rad(d, gw_na=None, gw_liste=None):
    kls = d.get("medalje") or ""
    badge = (
        f'<img class="lb-badge" src="{escape(d["badge"])}" alt="">'
        if d.get("badge")
        else '<span class="lb-badge tom"></span>'
    )

    # Oppbrukte chips tett paa navnet, aktiv chip ute i meta-kolonnen.
    # Fast slisse per type saa de flukter loddrett mellom radene.
    har = set(d.get("brukte_chips") or [])
    brukt = "".join(
        f'<span class="brukt-chip">{c}</span>' if c in har else "<span></span>"
        for c in CHIP_REKKEFOLGE
    )

    ringer = (" beste" if d.get("har_beste_gw") else "") + (" verst" if d.get("har_verste_gw") else "")
    hint = []
    if d.get("har_beste_gw"):
        hint.append(f'Beste enkeltrunde: {d["beste_gw"]} poeng')
    if d.get("har_verste_gw"):
        hint.append(f'Verste enkeltrunde: {d["verste_gw"]} poeng')
    tittel = f' title="{escape(" · ".join(hint))}"' if hint else ""

    # Fullt navn paa TV, forkortelse paa mobil. Begge rendres, CSS velger.
    aktiv_chip = (
        f'<span class="chip-badge"><span class="lang">{escape(d["chip"])}</span>'
        f'<span class="kort">{escape(d.get("chip_kort") or "")}</span></span>'
        if d.get("chip")
        else ""
    )
    kaptein = f'<span class="kaptein"><b>C</b>{escape(d["kaptein"])}</span>' if d.get("kaptein") else ""

    premie = "".join(
        f'<span class="premie {pr["type"]}">kr&nbsp;{pr["kr"]:,}'.replace(",", "&thinsp;") + ",&ndash;</span>"
        for pr in d.get("premier") or []
    )

    return f"""      <details class="lb-item">
        <summary class="lb-row {kls}">
          <div class="premier">{premie}</div>
          {_pil(d["rank"], d.get("forrige_rank"))}
          <div class="lb-rank{ringer}"{tittel}>{d["rank"]}</div>
          {badge}
          <div class="lb-navn">
            <div class="lb-lagnavn">{escape(d["lagnavn"])}</div>
            <div class="lb-fornavn">{escape(d["fornavn"])}</div>
          </div>
          <div class="mobil-linje">
            <div class="brukt-chips">{brukt}</div>
            <div class="spacer"></div>
            <div class="meta-chip">{aktiv_chip}</div>
          </div>
          <div class="meta-kaptein">{kaptein}</div>
          <div class="lb-gw">{d["gw_poeng"]}</div>
          <div class="lb-tot">{d["total"]}</div>
          <div class="utvid">&#9656;</div>
        </summary>
        <div class="detalj">{detalj(d, gw_na, gw_liste)}</div>
      </details>"""


def _kolonne(deltakere, gw_na=None, gw_liste=None):
    rader = "\n".join(_rad(d, gw_na, gw_liste) for d in deltakere)
    return f"""    <div class="col">
      <div class="col-head">
        <div class="pil"></div><div class="h-rank">#</div>
        <div class="lb-badge"></div><div>Deltaker</div>
        <div class="mobil-linje">
          <div class="brukt-chips"></div><div class="spacer"></div>
          <div class="meta-chip"></div>
        </div>
        <div class="meta-kaptein"></div>
        <div class="h-gw">GW</div><div class="h-tot">Tot</div>
        <div class="utvid"></div>
      </div>
{rader}
    </div>"""


def render(data):
    d = data["deltakere"]
    k = data["kamper"]
    gw = data["gw"]
    gw_liste = data.get("gw_liste") or []

    dempet = 'style="color:var(--muted);background:none;border-color:var(--line)"'
    igjen = k["totalt"] - k["ferdig"]
    if data["live"]:
        status = f'<span class="status"><span class="dot"></span>{k["live"]} kamper pågår</span>'
    elif gw["ferdig"]:
        status = f'<span class="status" {dempet}>{escape(gw["navn"])} ferdig</span>'
    elif not igjen:
        status = f'<span class="status" {dempet}>alle kamper spilt</span>'
    elif k["ferdig"]:
        # Pause mellom kampdagene - «venter paa avspark» ville vaert feil naar
        # over halve runden allerede er spilt.
        status = f'<span class="status" {dempet}>{igjen} kamper igjen</span>'
    else:
        status = f'<span class="status" {dempet}>venter på avspark</span>'

    # To kolonner naar gjengen vokser forbi det en TV-hoeyde taaler i én kolonne.
    # Tavler som ikke staar paa en TV setter en_kolonne og scroller i stedet -
    # da beholder de klubblogo, aktiv chip og kaptein i raden.
    if len(d) > 12 and not data.get("en_kolonne"):
        midt = (len(d) + 1) // 2
        board_kls = "board to-kolonner"
        kolonner = _kolonne(d[:midt], gw["id"], gw_liste) + "\n" + _kolonne(d[midt:], gw["id"], gw_liste)
    else:
        board_kls = "board"
        kolonner = _kolonne(d, gw["id"], gw_liste)

    pct = round(100 * k["ferdig"] / k["totalt"]) if k["totalt"] else 0
    pct_live = round(100 * k["live"] / k["totalt"]) if k["totalt"] else 0
    live_linje = f'<div class="gw-live">{k["live"]} pågår nå</div>' if k["live"] else ""
    oppdatert = _norsk_tid(data.get("sist_oppdatert") or data["generert"])

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
        <div class="tegnforklaring">
          <span class="tf"><span class="tf-ring">6</span>Beste enkeltrunde</span>
          <span class="tf"><span class="tf-ring verst">9</span>Verste enkeltrunde</span>
          <span class="tf"><span class="chip-badge">Bench Boost</span>Chip i spill</span>
          <span class="tf"><span class="brukt-chip">BB</span>Chip brukt opp</span>
        </div>
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

  <footer>Oppdatert {oppdatert}</footer>
</div>
<script>
/* Blar mellom gameweeks i en utfelling. Hver runde ligger ferdig rendret i
   lag/GW-filene, saa vi bytter bare ut innholdet - ingen logikk duplisert
   mellom Python og JavaScript. Sida fungerer uten dette skriptet; da staar
   den bare paa gjeldende runde.
   NB: dette ligger i en f-string, saa alle kroellparenteser maa dobles. */
document.addEventListener('click', function (e) {{
  var knapp = e.target.closest('.gw-pil');
  if (!knapp || knapp.classList.contains('av')) return;
  var nav = knapp.closest('.gw-nav');
  var boks = knapp.closest('.detalj');
  boks.classList.add('laster');
  fetch('lag/GW' + knapp.dataset.gw + '.json')
    .then(function (r) {{ return r.json(); }})
    .then(function (j) {{
      var html = j[nav.dataset.entry];
      if (html) boks.innerHTML = html;
      boks.classList.remove('laster');
    }})
    .catch(function () {{ boks.classList.remove('laster'); }});
}});
</script>
</body>
</html>
"""
