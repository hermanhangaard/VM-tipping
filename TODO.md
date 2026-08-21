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

- [ ] Installer `gh`: `sudo apt install gh` (2.45 i repo), så `gh auth login`
- [ ] Opprett public repo `hermanhangaard/fpl`
- [ ] Fjern custom domain fra `VM-tipping` (Settings → Pages) FØR den settes på det nye repoet
- [ ] Settings → Pages → Source: **GitHub Actions** (ikke «Deploy from a branch») — slipper å committe HTML 2000 ganger i året
- [ ] Sett custom domain `hangaard.no`. DNS er allerede riktig, ingen endring hos Domeneshop
- [ ] Legg `CNAME` med innholdet `hangaard.no` i mappa som publiseres
- [ ] Hello-world-workflow først, før noe annet bygges:

```yaml
name: test
on: workflow_dispatch
jobs:
  hei:
    runs-on: ubuntu-latest
    steps:
      - run: curl -s "https://fantasy.premierleague.com/api/leagues-classic/562901/standings/" | head -c 500
```

  Actions-fanen → «test» → Run workflow. Ser du liganavnet i loggen, funker alt. Slett fila etterpå.

## Fase 2 — pipeline (lokalt)

`parser.py` og `score.py` fra VM-prosjektet faller bort — FPL regner poengene selv.

- [ ] `fpl_api.py` — henter bootstrap, standings, fixtures
- [ ] `navn.json` — engangs-henting av `player_first_name` per entry, committes. Kjøres på nytt ved ny deltaker
- [ ] `historikk.json` — poeng per deltaker per GW, akkumuleres hver kjøring. **Grunnlag for grafene — fås ikke i ettertid hvis den ikke lagres underveis**
- [ ] `render.py` → `dist/index.html`. Start fra `../vm-prosjekt-dev/fase2/render2.py`, bytt datamodell
- [ ] Kjør lokalt til HTML-en ser riktig ut. Ikke rør Actions før den stemmer

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
