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

ROT = Path(__file__).parent
DATA = ROT / "data"
DIST = ROT / "dist"

NAVN_FIL = DATA / "navn.json"
HISTORIKK_FIL = DATA / "historikk.json"

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


def hent_lag(entry_id, gw, spillere, live):
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
            "kaptein": bool(pick.get("is_captain")),
            "vise": bool(pick.get("is_vice_captain")),
        })

    hist = p.get("entry_history") or {}
    return {
        "kaptein": kaptein,
        "chip": CHIP_NAVN.get(p.get("active_chip") or ""),
        "benk": hist.get("points_on_bench"),
        "trekk": hist.get("event_transfers_cost") or 0,
        "tropp": tropp,
        # Bytter hentes fra entry/{id}/transfers/. Tom hele GW1 fordi sesongen
        # nettopp har startet - feltnavnene er derfor IKKE verifisert mot ekte
        # data enda. Foerste sjanse: GW2-deadline 28.08.
        "bytter": [],
    }


def bygg():
    bs = fpl_api.bootstrap()
    gw = fpl_api.naavaerende_gw(bs)
    gw_id = gw["id"]

    spillere = {e["id"]: e for e in bs["elements"]}
    lag = {t["id"]: t for t in bs["teams"]}

    tabell = fpl_api.standings()
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
        d.update(hent_lag(eid, gw_id, spillere, live_poeng))
        d.update(hent_historikk(eid, gw_id))
        # Beste enkeltrunde: ferdige GW-er fra history, inneværende fra
        # ligatabellen siden history henger etter.
        d["beste_gw"] = max([*d.get("gw_poeng_historikk", {}).values(), d["gw_poeng"]])
        deltakere.append(d)

    # Premie gaar til beste enkeltrunde i hele ligaen. Flere kan dele den.
    toppen = max((d["beste_gw"] for d in deltakere), default=0)
    for d in deltakere:
        d["har_beste_gw"] = bool(toppen) and d["beste_gw"] == toppen

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
        "lag": {str(k): v["short_name"] for k, v in lag.items()},
    }

    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(render.render(data), encoding="utf-8")

    # Pages serverer naa kun det artifacten inneholder. Uten CNAME i dist/
    # mister vi custom domain ved foerste deploy.
    shutil.copy(ROT / "CNAME", DIST / "CNAME")

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
    args = ap.parse_args()

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
