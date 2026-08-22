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
- [x] `Aasmund` og `Jarle Andre` skal stå som de er — bekreftet 22.08

## Fase 3 — workflow

Ligger i `.github/workflows/board.yml`. Kjører hvert 10. minutt (UTC) + `workflow_dispatch`.

- [x] Early exit i `build.py` → `bor_bygge()`. Bygger når (a) en kamp har `started && !finished`, (b) GW mangler i historikken, (c) GW ferdigspilt men `data_checked` ikke satt ennå (bonuspoeng låses først da), eller (d) >6 t siden sist. Ellers avslutt. Begge grener testet
- [x] `build.py` skriver `bygget=true/false` til `GITHUB_OUTPUT`; commit, artifact-opplasting og deploy er gated på den. Uten dette ville `upload-pages-artifact` feilet på bomturene fordi `dist/` ikke finnes
- [x] `data/` committes tilbake av `github-actions[bot]`. Dobbelt formål: bevarer historikken, og holder repoet aktivt mot 60-dagersregelen
- [x] Action-versjoner verifisert mot GitHub: `checkout@v7`, `setup-python@v7`, `upload-pages-artifact@v5`, `deploy-pages@v5`. **Alle var nyere enn det som sto her fra hukommelsen (v4/v5)** — sjekk på nytt ved neste større endring
- [x] `pip install requests` fjernet — `urllib` holder
- [x] Første kjøring verifisert: run 32587275979, 25 s, bygde + committet + deployet. hangaard.no svarer 200 med den nye tavla
- [x] `_get()` memoiseres per prosess — `bor_bygge()` og `bygg()` ba begge om bootstrap (1,5 MB)

- [x] `.github/workflows/test.yml` slettet
- [x] **Planlagt cron verifisert.** Run 32588413100, `event: schedule`, 17:39:51Z → 17:40:13Z, 22 s, success. Punktlig på `*/10` uten målbar forsinkelse. Første planlagte kjøring kom ca. 20 min etter at workflowen kom på `main` — GitHub bruker litt tid på å aktivere en ny `schedule:`

**Gjenstår:**
- [ ] Se at early exit oppfører seg riktig i Actions midt i uka, når det ikke er kamper (forventet logglinje: `hopper over: ingen kamper, sist bygget for N min siden`)

## Fase 4 — TV-visning

Stort sett gjort som del av Fase 2, siden `render.py` ble skrevet mot TV-kravet fra start.

- [x] `<meta http-equiv="refresh" content="300">`
- [x] Store fonter, høy kontrast. Skalering `clamp(15px, min(1.62vh, 1.45vw), 38px)` — målt mot 1920x1080 med 9 rader, header og footer. **Første forsøk (1.9vh) kuttet rad 9**, så dette er verifisert med headless-render, ikke antatt
- [x] Fornavn + lagnavn, aldri etternavn
- [x] Klubblogo via `club_badge_src` — implementert, men 6 av 9 mangler (se HUSK-punktet over)
- [x] Ny bakgrunn: PL-lilla gradient i stedet for VM-rødt
- [x] `noindex` lagt inn

**Gjenstår:**
- [x] Bevegelsespiler opp/ned, drevet av `last_rank`. Grønn ▲, rød ▼ (`--ned` #ff4d4d — ren rød vibrerer mot lilla), svak – ved uendret, ingenting når `last_rank` er 0. **Aktiveres først GW2 (28.08), så den er testet med syntetiske tall** — alle fire tilfeller verifisert i markup og på skjermbilde. Første størrelse (0.78rem) var for liten for TV, økt til 1.05rem
- [x] Bakgrunnsfoto `design/bakgrunn.jpg`, slørt 4px og mørklagt med gradient (svakest øverst, sterkest nederst der tavla ligger). Kilden er **686x386**, altså skalert ~2,8x opp — sløringen skjuler mye, men et høyoppløst bilde ville vært et reelt løft. Komposisjonen funker fordi motivene ligger i ytterkantene og tavla i den mørke midten
- [x] Utfellbar lagvisning per deltaker via `<details>`/`<summary>` — null JavaScript. Viser byttestripe, GW-poeng, bane med startellever gruppert K/F/M/A, benk, drakter fra PL sin CDN (`shirt_{team_code}[_1]-110.png`), kaptein/vise-merke og live-poeng per spiller. Validert mot Aasmund: 35 fra startellever + 17 fra benk (Bench Boost) = 52, nøyaktig GW-scoren

**Gjenstår:**
- [ ] Se tavla på den faktiske TV-en før GW2. Alt er verifisert på 1920x1080 headless — Lasses skjerm kan ha annen oppløsning eller overscan
- [ ] **Byttestripa står tom med vilje.** `entry/{id}/transfers/` svarer 200 med en liste, men den er tom for alle fordi ingen har byttet ennå i sesongen. Feltnavnene (`element_in`, `element_out`, `event`, kostnad) er fra hukommelsen og **ikke observert**. Verifiser mot ekte data ved GW2-deadline fredag 28.08 19:30, og sjekk samtidig om bytter i det hele tatt er synlige før deadline
- [ ] Vurder høyoppløst erstatning for bakgrunnen hvis den skal bli permanent
- [ ] Drop-downen er usynlig på TV-en — den kan ikke klikkes. Funksjonen er for telefon/PC

## Fase 5 — drift

- [ ] Verifiser oppdatering under GW1 (kamper fre 21.08 21:00, lør, søn, man 24.08 21:00)
- [ ] **Sjekk at scheduled workflows fortsatt kjører etter landslagspausen i oktober** — GitHub deaktiverer dem etter 60 dager uten repo-aktivitet. `historikk.json`-commitene bør holde den i live, men usikkert om bot-commits teller
- [ ] Slett den gamle lokale cronjobben (`../vm-prosjekt-dev/fase2/cron_run2.sh`, `*/5 * * * *`) når dette er live

---

## Utenfor dette prosjektet

**Graf-greiene hører IKKE hjemme her.** `graf/`-koden i `../vm-prosjekt-dev/` er knyttet til et annet domene og et annet GitHub-repo. Ikke bland den inn i `fpl/`, og ikke kopier kode derfra uten å avklare først. Eventuell historikk-visualisering for FPL er et eget prosjekt vi kan ta senere — `data/historikk.json` samler grunnlaget i mellomtiden, men det er alt.

## Notater

- Actions `schedule:` er upresis — 5–20 min forsinkelse er vanlig under last, og jobber kan droppes. Ikke design for presisjon. Pages-CDN cacher ~10 min uansett
- Public repo = gratis og ubegrensede Actions-minutter
- Bonuspoeng er ikke endelige før kampen er ferdig: `bps` er live, `bonus` blir provisorisk og så bekreftet
- Auto-subs (`automatic_subs`) fylles først når GW er ferdig
- Global CLAUDE.md sier «ingen git installert lokalt» — det stemmer ikke, `/usr/bin/git` finnes og SSH-push mot GitHub er verifisert
