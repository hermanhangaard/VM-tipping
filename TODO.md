# FPL-tavle — Norconsult Sarpsborg 26/27

Ledertavle for FPL-mini-ligaen, vises på TV hos Lasse. Etterfølger til VM-tippeprosjektet (`../vm-prosjekt-dev/`).

## Fakta

| | |
|---|---|
| Liga | Norconsult Sarpsborg 26/27 |
| Liga-ID | `562901` (classic, privat, `start_event: 1`) |
| Admin | entry 2795526 (Are Stifjell) — ikke Herman |
| Deltakere | 9 per 21.08.2026, `closed: false` |
| Sesong | GW1 deadline 21.08.2026 19:30 norsk → GW38 30.05.2027 |
| API | `https://fantasy.premierleague.com/api/` — gratis, ingen nøkkel, ingen kvote observert |
| Domene | hangaard.no (Domeneshop DNS → GitHub Pages, A-records 185.199.108-111.153) |

Personvern: **kun fornavn + lagnavn**, aldri etternavn. Klarert med Are/Lasse. Bruk `player_first_name` fra `entry/{id}/` — ikke split `player_name` på mellomrom (gir «Hans» av «Hans Magnus»).

## Endepunkter

| Endepunkt | Innhold |
|---|---|
| `bootstrap-static/` | 600 spillere x 109 felt, 20 lag, 38 GW-er, chips. 1,5 MB |
| `leagues-classic/562901/standings/` | Tabellen. 1 kall, 50 per side |
| `entry/{id}/` | Manager: fornavn, lagnavn, totalpoeng, rank, lagverdi |
| `entry/{id}/history/` | Poeng/rank/transfers per GW + tidligere sesonger + chips |
| `entry/{id}/event/{gw}/picks/` | 15 spillere, kaptein, benk, aktiv chip, auto-subs |
| `event/{gw}/live/` | Live-stats per spiller inkl. bps, bonus, xG/xA, poeng-brekkdown |
| `fixtures/?event={gw}` | Kamper, stilling, kickoff, FDR |
| Draktbilde | `resources.premierleague.com/premierleague/photos/players/250x250/p{code}.png` |
| Klubblogo | `resources.premierleague.com/premierleague/badges/rb/t{team_code}.svg` |

Ikke tilgjengelig: `my-team/{id}/` (403, krever innlogging). CORS er stengt — nettleseren kan ikke hente API-et direkte, så HTML må genereres server-side.

---

## Fase 0 — beslutninger

- [x] Overskriv hangaard.no. VM-tavla trengs ikke lenger (den overlever automatisk på `hermanhangaard.github.io/VM-tipping/` når custom domain fjernes).
- [x] Klarert offentlig visning med Are/Lasse.
- [x] Arkitektur: ett public repo, alt i GitHub Actions. Ingen to-mappers-splitt — det fantes ingen hemmeligheter å skjerme (ingen API-nøkkel, ingen tippeark).

## Fase 1 — GitHub-oppsett

Workflow = YAML-fil i `.github/workflows/`. Kjører på en fersk Ubuntu-VM (runner) som slettes etterpå — ingenting persisteres uten commit eller artifact-opplasting. Kjøringer vises under Actions-fanen.

- [x] Installer `gh` (2.45) + `gh auth login`. Scopes: `gist, read:org, repo, workflow`
- [x] Gjenbruk eksisterende repo framfor å lage nytt: `gh repo rename fpl` på `VM-tipping`. Custom domain og HTTPS-sertifikat fulgte med — `hangaard.no` var aldri nede
- [x] `git gc --prune=now` → 5,0 GB løse objekter ned til 80 MB. GitHub rapporterte uansett bare 29 MB
- [x] Lokal mappe `personal/vm-prosjekt` → `personal/fpl`. Remote oppdatert til `git@github.com:hermanhangaard/fpl.git`
- [x] Pages `build_type: legacy` → `workflow` via `gh api -X PUT repos/hermanhangaard/fpl/pages -f build_type=workflow`
- [x] Hello-world-workflow kjørt (`.github/workflows/test.yml`, run 32516030033, 11s, success) — leste ut alle 9 deltakerne fra API-et
- [ ] Slett `test.yml` når `board.yml` er på plass. Beholdt inntil videre som manuell røyktest
- [ ] `CNAME` med innholdet `hangaard.no` må inn i `dist/` — Pages serverer nå kun det artifacten inneholder, ikke repo-rota
- [ ] Slett `index.html` fra rota (VM-tavla, 3,2 MB). Ligger i historikken hvis den trengs

## Fase 2 — pipeline (lokalt)

`parser.py` og `score.py` fra VM-prosjektet faller bort — FPL regner poengene selv.

- [x] `fpl_api.py` — bootstrap, standings, entry, picks, fixtures. `urllib` framfor `requests`, så ingen `pip install` noe sted. Retry med backoff (FPL gir sporadiske SSL-brudd, jf. football-data.org-mønsteret)
- [x] `data/navn.json` — `player_first_name` per entry, hentes kun for ukjente ider. Håndredigerbar
- [x] `data/historikk.json` — `{gw: {entry: {p, tot, rank}}}`, akkumuleres hver kjøring
- [x] `render.py` → `dist/index.html`. PL-palett (#37003c-lilla, `--gronn` #00ff87, `--cyan` #04f5ff) i stedet for VM-rødt. Samme grep ellers: flytende vh-skalering, kortbasert tavle, gull/sølv/bronse
- [x] `build.py` — orkestrator. Kopierer også `CNAME` inn i `dist/`
- [x] Verifisert mot ekte GW1-data (9 deltakere, live-kamper) og skjermbilde på 1920x1080
- [x] `index.html` (VM-tavla) slettet fra rota, `dist/` lagt i `.gitignore`

Kjør lokalt: `python3 build.py`, åpne `dist/index.html`.

**Åpne punkter:**
- [x] `Torbjorn` → `Torbjørn` rettet manuelt i `data/navn.json`. `build.py` henter kun ukjente ider, så rettelsen overlever. Samme grep for framtidige navn med æøå
- [x] ~~Egen live-poengberegning~~ — **ikke nødvendig.** Målt 22.08 med 6 kamper live: ligatabellens `event_total` matcher en fra bunnen av utregning (`event/{gw}/live/` × multiplier − transferkost) med **0 avvik for alle 9**. Endepunktet er allerede live. Reell forsinkelse mot tlf-appen er 5-min meta-refresh + ~10 min Pages-CDN, altså leveranse og ikke data
- [ ] **HUSK: spør Lasse om klubblogoene.** Bare 3 av 9 har `club_badge_src` satt — resten får tom sirkel. Enten får folk sette favorittklubb i FPL-profilen sin, eller så dropper vi kolonnen
- [ ] Sjekk om `Aasmund` og `Jarle Andre` skal ha `Åsmund` / `André`. Ikke endret på eget initiativ — «Aasmund» er en gyldig skrivemåte, og feil retting er verre enn ingen retting

## Fase 3 — workflow

`.github/workflows/board.yml`:

```yaml
name: FPL board
on:
  schedule:
    - cron: '*/10 * * * *'      # NB: UTC, ikke norsk tid
  workflow_dispatch:

permissions:
  contents: write               # for å committe historikk.json
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install requests
      - run: python build.py
      - uses: actions/upload-pages-artifact@v3
        with: { path: dist }
      - uses: actions/deploy-pages@v4
```

- [ ] Early exit i `build.py`: full pipeline kun hvis (a) en kamp har `started: true, finished: false`, (b) siste kjøring >6t siden, eller (c) manuelt trigget. Bomturene er gratis, men loggen skal være lesbar
- [ ] Commit `historikk.json` tilbake i samme jobb
- [ ] Verifiser action-versjonene mot GitHub sine repos — v4/v5 er skrevet fra hukommelsen, de bumpes jevnlig

## Fase 4 — TV-visning

- [ ] `<meta http-equiv="refresh" content="300">` (beholdes fra VM-oppsettet)
- [ ] Store fonter, høy kontrast — samme smertepunkter som sist
- [ ] Fornavn + lagnavn, aldri etternavn
- [ ] Klubblogo per deltaker via `club_badge_src` (ligger ferdig i standings-svaret)
- [ ] Ny bakgrunn
- [ ] Vurder `noindex` — dataene ligger allerede åpent i API-et, men er ikke søkbare på Google i dag

## Fase 5 — drift

- [ ] Verifiser oppdatering under GW1 (kamper fre 21.08 21:00, lør, søn, man 24.08 21:00)
- [ ] **Sjekk at scheduled workflows fortsatt kjører etter landslagspausen i oktober** — GitHub deaktiverer dem etter 60 dager uten repo-aktivitet. `historikk.json`-commitene bør holde den i live, men usikkert om bot-commits teller
- [ ] Slett den gamle lokale cronjobben (`../vm-prosjekt-dev/fase2/cron_run2.sh`, `*/5 * * * *`) når dette er live

---

## Notater

- Actions `schedule:` er upresis — 5–20 min forsinkelse er vanlig under last, og jobber kan droppes. Ikke design for presisjon. Pages-CDN cacher ~10 min uansett
- Public repo = gratis og ubegrensede Actions-minutter
- Bonuspoeng er ikke endelige før kampen er ferdig: `bps` er live, `bonus` blir provisorisk og så bekreftet
- Auto-subs (`automatic_subs`) fylles først når GW er ferdig
- Global CLAUDE.md sier «ingen git installert lokalt» — det stemmer ikke, `/usr/bin/git` finnes og SSH-push mot GitHub er verifisert
