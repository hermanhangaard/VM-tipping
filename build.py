#!/usr/bin/env python3
"""Bygger hangaard.no: henter FPL-data, oppdaterer historikk, skriver dist/index.html.

Kjoeres lokalt under utvikling og fra .github/workflows/board.yml i drift.
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import fpl_api
import render

# Rota settes av --rot, saa den samme koden kan bygge flere ligaer fra hvert
# sitt datarepo. Uten flagget bygger den prosjektet den selv ligger i.
ROT = Path(__file__).parent
DATA = DIST = LAG_DIR = NAVN_FIL = HISTORIKK_FIL = None
LIGA_ID = None
KONFIG = {}


def sett_rot(rot):
    """Peker alle stier og liga-ID mot ett prosjekt."""
    global ROT, DATA, DIST, LAG_DIR, NAVN_FIL, HISTORIKK_FIL, LIGA_ID
    ROT = Path(rot).resolve()
    DATA, DIST = ROT / "data", ROT / "dist"
    NAVN_FIL, HISTORIKK_FIL, LAG_DIR = DATA / "navn.json", DATA / "historikk.json", DATA / "lag"
    global KONFIG
    KONFIG = json.loads((ROT / "konfig.json").read_text(encoding="utf-8"))
    LIGA_ID = KONFIG["liga_id"]

# data/lag/GW{n}.json: én fil per gameweek med tropp, bytter og poeng.
# En ferdigspilt runde endrer seg aldri, saa den skrives én gang og hentes
# aldri fra API-et igjen. Uten dette ville full historikk kostet 342 API-kall
# og 15,8 MB per bygg.

CHIP_NAVN = {
    "3xc": "Triple Captain",
    "bboost": "Bench Boost",
    "freehit": "Free Hit",
    "wildcard": "Wildcard",
}
CHIP_KORT = {"3xc": "TC", "bboost": "BB", "freehit": "FH", "wildcard": "WC"}


def halvdel_start(gw):
    """FPL gir alle chips paa nytt fra GW20. En chip brukt foer det er derfor
    ikke «brent» lenger naar andre halvdel starter."""
    return 1 if gw < 20 else 20


def hent_historikk(entry_id, gw):
    """Poeng per ferdigspilt GW + hvilke chips som er brukt.

    NB: history/current henger etter for inneværende runde - den viser
    delvise tall til FPL har avregnet. Poeng for gjeldende GW maa derfor
    hentes fra ligatabellen, ikke herfra.
    """
    try:
        h = fpl_api._get(f"entry/{entry_id}/history/")
    except RuntimeError:
        return {}
    return {
        "gw_poeng_historikk": {r["event"]: r["points"] for r in h.get("current", []) if r["event"] != gw},
        "brukte_chips": [
            CHIP_KORT[c["name"]]
            for c in h.get("chips", [])
            if c["name"] in CHIP_KORT and halvdel_start(gw) <= c["event"] < gw
        ],
    }


def les_json(sti, standard):
    if sti.exists():
        return json.loads(sti.read_text(encoding="utf-8"))
    return standard


def skriv_json(sti, data):
    sti.parent.mkdir(parents=True, exist_ok=True)
    sti.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def hent_fornavn(entry_ider, cache):
    """player_first_name fra entry-endepunktet. Autoritativt - «Hans Magnus» blir
    ikke «Hans», slik en split paa mellomrom ville gitt. Navn endrer seg ikke,
    saa vi henter kun for ukjente ider."""
    nye = 0
    for eid in entry_ider:
        if str(eid) in cache:
            continue
        d = fpl_api.entry(eid)
        cache[str(eid)] = d["player_first_name"]
        nye += 1
    return nye


def hent_bytter(entry_id, gw, spillere):
    """Overganger gjort til gjeldende GW.

    Feltnavnene (element_in/element_out/event) er verifisert mot ekte data
    31.08. De var ikke observerbare foer det, siden ingen hadde byttet enda -
    GW1 har per definisjon ingen overganger.
    """
    try:
        alle = fpl_api._get(f"entry/{entry_id}/transfers/")
    except RuntimeError:
        return []

    bytter = []
    for t in alle:
        if t["event"] != gw:
            continue
        inn, ut = spillere.get(t["element_in"]), spillere.get(t["element_out"])
        if inn and ut:
            bytter.append({"ut": ut["web_name"], "inn": inn["web_name"]})
    # API-et gir nyeste foerst; snu saa de staar i byttet raekkefoelge.
    return list(reversed(bytter))


def motstandere(kamper, lag):
    """lag-id -> «AVL (A)» for kamper som ikke har startet enda.

    Bare kamper som ikke er i gang teller. Har kampen begynt og spilleren
    likevel null minutter, satt han paa benken - da skal det staa strek, ikke
    en motstander som om kampen laa foran ham.
    Dobbeltrunder gir flere kamper i lista - alle vises. Blanke runder: laget
    mangler i mappingen og faller tilbake paa strek.
    """
    ut = {}
    for f in sorted(kamper, key=lambda x: x["kickoff_time"] or ""):
        if f["started"]:
            continue
        ut.setdefault(f["team_h"], []).append(f"{lag[f['team_a']]} (H)")
        ut.setdefault(f["team_a"], []).append(f"{lag[f['team_h']]} (A)")
    return ut


def hent_lag(entry_id, gw, spillere, live, mot=None):
    """Tropp, kaptein, chip og benkepoeng for en manager.

    picks er tomt foer deadline - da faar vi RuntimeError og returnerer {}.
    posisjon 1-11 er startellever, 12-15 er benk.
    """
    try:
        p = fpl_api.picks(entry_id, gw)
    except RuntimeError:
        return {}

    kaptein = None
    tropp = []
    for pick in p.get("picks", []):
        sp = spillere.get(pick["element"])
        if not sp:
            continue
        raa, minutter = live.get(pick["element"], (0, 0))
        if pick.get("is_captain"):
            kaptein = sp["web_name"]
        tropp.append({
            "navn": sp["web_name"],
            "type": sp["element_type"],
            "lag_kode": sp["team_code"],
            "posisjon": pick["position"],
            "mult": pick["multiplier"],
            # Startellever viser bidraget sitt (kaptein dobbelt), benken raa poeng.
            "poeng": raa * pick["multiplier"] if pick["multiplier"] else raa,
            "spilt": minutter > 0,
            "motstander": None if minutter > 0 else (mot or {}).get(sp["team"]),
            "kaptein": bool(pick.get("is_captain")),
            "vise": bool(pick.get("is_vice_captain")),
        })

    hist = p.get("entry_history") or {}
    return {
        "kaptein": kaptein,
        "chip": CHIP_NAVN.get(p.get("active_chip") or ""),
        # Mobilvisningen har ikke plass til «Triple Captain» - den bruker
        # forkortelsen, samme som de oppbrukte chipsene.
        "chip_kort": CHIP_KORT.get(p.get("active_chip") or ""),
        "benk": hist.get("points_on_bench"),
        "trekk": hist.get("event_transfers_cost") or 0,
        "tropp": tropp,
        "bytter": hent_bytter(entry_id, gw, spillere),
    }


def lagre_gw(gw_id, deltakere, ferdig):
    """Fryser en gameweek til disk. Skrives paa nytt hver kjoering saa lenge
    runden paagaar; naar den er ferdigspilt roeres fila aldri mer."""
    fil = LAG_DIR / f"GW{gw_id}.json"
    if fil.exists() and les_json(fil, {}).get("ferdig"):
        return False
    skriv_json(fil, {
        "gw": gw_id,
        "ferdig": ferdig,
        "deltakere": {
            str(d["entry"]): {
                "lagnavn": d["lagnavn"],
                "fornavn": d["fornavn"],
                "gw_poeng": d["gw_poeng"],
                "trekk": d.get("trekk") or 0,
                "kaptein": d.get("kaptein"),
                "chip": d.get("chip"),
                "bytter": d.get("bytter") or [],
                "har_beste_gw": d.get("har_beste_gw", False),
                "har_verste_gw": d.get("har_verste_gw", False),
                "beste_gw_nr": d.get("beste_gw_nr"),
                "verste_gw_nr": d.get("verste_gw_nr"),
                "tropp": d.get("tropp") or [],
            }
            for d in deltakere
        },
    })
    return True


def backfyll(rader, spillere, til_og_med, kortnavn):
    """Henter og fryser gameweeks vi mangler. Kjoeres én gang per runde som
    mangler - deretter ligger de paa disk for godt."""
    for gw in range(1, til_og_med):
        if (LAG_DIR / f"GW{gw}.json").exists():
            continue
        print(f"backfyller GW{gw} ...")
        live = {
            e["id"]: (e["stats"]["total_points"], e["stats"]["minutes"])
            for e in fpl_api._get(f"event/{gw}/live/")["elements"]
        }
        deltakere = []
        for r in rader:
            eid = r["entry"]
            h = fpl_api._get(f"entry/{eid}/history/")
            poeng = next((x["points"] for x in h.get("current", []) if x["event"] == gw), 0)
            d = {"entry": eid, "lagnavn": r["entry_name"],
                 "fornavn": les_json(NAVN_FIL, {}).get(str(eid), ""), "gw_poeng": poeng}
            d.update(hent_lag(eid, gw, spillere, live, motstandere(fpl_api.fixtures(gw), kortnavn)))
            deltakere.append(d)
        lagre_gw(gw, deltakere, ferdig=True)


def kjente_gw():
    """Gameweeks vi har bufret, i stigende raekkefoelge."""
    if not LAG_DIR.exists():
        return []
    return sorted(int(f.stem[2:]) for f in LAG_DIR.glob("GW*.json"))


def bygg():
    bs = fpl_api.bootstrap()
    gw = fpl_api.naavaerende_gw(bs)
    gw_id = gw["id"]

    spillere = {e["id"]: e for e in bs["elements"]}
    lag = {t["id"]: t for t in bs["teams"]}

    tabell = fpl_api.standings(LIGA_ID)
    rader = tabell["standings"]["results"]
    kamper = fpl_api.fixtures(gw_id)

    # Poeng og spilletid per spiller akkurat naa - grunnlaget for banevisningen.
    # minutes skiller «har ikke spilt enda» fra «spilte og fikk 0».
    live_poeng = {
        e["id"]: (e["stats"]["total_points"], e["stats"]["minutes"])
        for e in fpl_api._get(f"event/{gw_id}/live/")["elements"]
    }

    # finished settes foerst naar FPL har laast bonuspoengene, ofte timer etter
    # sluttsignalet. finished_provisional er «kampen er spilt ferdig», som er
    # det tavla skal vise.
    ferdig = sum(1 for f in kamper if f["finished_provisional"])
    live = sum(1 for f in kamper if f["started"] and not f["finished_provisional"])

    kortnavn = {t2["id"]: t2["short_name"] for t2 in bs["teams"]}
    mot = motstandere(kamper, kortnavn)

    navn = les_json(NAVN_FIL, {})
    nye = hent_fornavn([r["entry"] for r in rader], navn)
    if nye:
        skriv_json(NAVN_FIL, navn)
        print(f"navn.json: hentet {nye} nye fornavn")

    deltakere = []
    for r in rader:
        eid = r["entry"]
        d = {
            "entry": eid,
            "fornavn": navn.get(str(eid), r["player_name"].split()[0]),
            "lagnavn": r["entry_name"],
            "rank": r["rank"],
            "forrige_rank": r["last_rank"] or None,
            "gw_poeng": r["event_total"],
            "total": r["total"],
            "badge": r.get("club_badge_src"),
        }
        d.update(hent_lag(eid, gw_id, spillere, live_poeng, mot))
        d.update(hent_historikk(eid, gw_id))
        # Beste enkeltrunde: ferdige GW-er fra history, inneværende fra
        # ligatabellen siden history henger etter.
        runder = {**d.get("gw_poeng_historikk", {}), gw_id: d["gw_poeng"]}
        d["beste_gw"] = max(runder.values())
        d["verste_gw"] = min(runder.values())
        # Ved likt resultat viser vi den seneste runden - den er mest aktuell.
        d["beste_gw_nr"] = max(g for g, poeng in runder.items() if poeng == d["beste_gw"])
        d["verste_gw_nr"] = max(g for g, poeng in runder.items() if poeng == d["verste_gw"])
        deltakere.append(d)

    # Beste og verste enkeltrunde i hele ligaen. Flere kan dele hver av dem,
    # og samme person kan eie begge.
    toppen = max((d["beste_gw"] for d in deltakere), default=0)
    bunnen = min((d["verste_gw"] for d in deltakere), default=0)
    for d in deltakere:
        d["har_beste_gw"] = bool(toppen) and d["beste_gw"] == toppen
        d["har_verste_gw"] = d["verste_gw"] == bunnen

    # Frys gjeldende runde, og hent inn eventuelle tidligere runder vi mangler.
    backfyll(rader, spillere, gw_id, kortnavn)
    lagre_gw(gw_id, deltakere, ferdig=bool(gw.get("data_checked")))
    gw_liste = kjente_gw()

    # Historikk akkumuleres underveis - FPL gir oss ikke ligarangeringen tilbake i tid,
    # saa mister vi denne fila mister vi grunnlaget for grafene.
    historikk = les_json(HISTORIKK_FIL, {})
    historikk[str(gw_id)] = {
        str(d["entry"]): {"p": d["gw_poeng"], "tot": d["total"], "rank": d["rank"]}
        for d in deltakere
    }
    skriv_json(HISTORIKK_FIL, historikk)

    data = {
        "liga": tabell["league"]["name"],
        "gw": {"id": gw_id, "navn": gw["name"], "ferdig": gw["finished"]},
        "kamper": {"ferdig": ferdig, "live": live, "totalt": len(kamper)},
        "live": live > 0,
        "sist_oppdatert": tabell.get("last_updated_data"),
        "generert": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "deltakere": deltakere,
        "gw_liste": gw_liste,
        "en_kolonne": KONFIG.get("en_kolonne", False),
        "lag": {str(k): v["short_name"] for k, v in lag.items()},
    }

    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(render.render(data), encoding="utf-8")

    # Pages serverer naa kun det artifacten inneholder. Uten CNAME i dist/
    # mister vi custom domain ved foerste deploy.
    shutil.copy(ROT / "CNAME", DIST / "CNAME")

    # Forhaandsrendre hver bufret runde til dist/lag/, saa pilene kan hente
    # dem uten aa vaere avhengige av API-et. Rendres paa nytt hvert bygg fra
    # de bufrede dataene, saa en designendring slaar gjennom overalt.
    lag_dist = DIST / "lag"
    lag_dist.mkdir(parents=True, exist_ok=True)
    for n in gw_liste:
        rundedata = les_json(LAG_DIR / f"GW{n}.json", {})
        skriv_json(lag_dist / f"GW{n}.json", {
            eid: render.detalj({**v, "entry": int(eid)}, n, gw_liste)
            for eid, v in rundedata.get("deltakere", {}).items()
        })

    bakgrunn = ROT / "design" / "bakgrunn.jpg"
    if bakgrunn.exists():
        shutil.copy(bakgrunn, DIST / "bakgrunn.jpg")

    return data


def bor_bygge():
    """Sier fra om det er verdt aa kjoere hele pipelinen.

    Cron gaar hvert 10. minutt hele aaret, men det skjer bare noe ~3 dager i uka.
    Vi bygger naar en kamp er i gang, naar GW nettopp ble ferdig (bonuspoeng
    laases foerst da), eller hvis det er over 6 timer siden sist - saa siden ikke
    staar og roter med et gammelt tidsstempel gjennom uka.

    Returnerer (bygg: bool, grunn: str). Koster ett API-kall.
    """
    bs = fpl_api.bootstrap()
    gw = fpl_api.naavaerende_gw(bs)
    kamper = fpl_api.fixtures(gw["id"])

    if any(f["started"] and not f["finished_provisional"] for f in kamper):
        return True, "kamp paagaar"

    historikk = les_json(HISTORIKK_FIL, {})
    if str(gw["id"]) not in historikk:
        return True, f"GW{gw['id']} ikke i historikken enda"

    # Etter sluttsignalet justeres bonuspoengene fortsatt til FPL har
    # data_checked. Vi maa fortsette aa bygge gjennom det vinduet.
    if not gw.get("data_checked") and any(f["finished_provisional"] for f in kamper):
        return True, "kamper spilt, venter paa endelige bonuspoeng"

    forrige = les_json(DATA / "sist.json", {}).get("tid")
    if forrige:
        alder = (datetime.now(timezone.utc) - datetime.fromisoformat(forrige)).total_seconds()
        if alder < 6 * 3600:
            return False, f"ingen kamper, sist bygget for {int(alder / 60)} min siden"
    return True, "over 6 timer siden sist"


def sett_output(bygget):
    """Forteller workflowen om det finnes en dist/ aa deploye."""
    fil = os.environ.get("GITHUB_OUTPUT")
    if fil:
        with open(fil, "a", encoding="utf-8") as f:
            f.write(f"bygget={'true' if bygget else 'false'}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="bygg uansett (hopper over live-sjekk)")
    ap.add_argument("--rot", default=Path(__file__).parent,
                    help="prosjektmappe med konfig.json, data/ og design/")
    args = ap.parse_args()
    sett_rot(args.rot)

    if not args.force:
        bygg_na, grunn = bor_bygge()
        print(f"{'bygger' if bygg_na else 'hopper over'}: {grunn}")
        if not bygg_na:
            sett_output(False)
            return 0

    data = bygg()
    skriv_json(DATA / "sist.json", {"tid": data["generert"]})
    sett_output(True)
    k = data["kamper"]
    status = "LIVE" if data["live"] else ("ferdig" if data["gw"]["ferdig"] else "venter")
    print(f"GW{data['gw']['id']} [{status}] - {k['ferdig']}/{k['totalt']} ferdig, {k['live']} paagaar")
    print(f"{len(data['deltakere'])} deltakere, leder: {data['deltakere'][0]['lagnavn']} "
          f"({data['deltakere'][0]['total']} p)")
    print(f"skrev {DIST / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
