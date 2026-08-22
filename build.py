#!/usr/bin/env python3
"""Bygger hangaard.no: henter FPL-data, oppdaterer historikk, skriver dist/index.html.

Kjoeres lokalt under utvikling og fra .github/workflows/board.yml i drift.
"""

import argparse
import json
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
    "manager": "Assistant Manager",
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


def hent_lag(entry_id, gw, spillere):
    """Kaptein, chip og benkepoeng for en manager. Returnerer tomt dict foer deadline."""
    try:
        p = fpl_api.picks(entry_id, gw)
    except RuntimeError:
        return {}

    kaptein = None
    for pick in p.get("picks", []):
        if pick.get("is_captain"):
            sp = spillere.get(pick["element"])
            if sp:
                kaptein = sp["web_name"]
            break

    hist = p.get("entry_history") or {}
    return {
        "kaptein": kaptein,
        "chip": CHIP_NAVN.get(p.get("active_chip") or ""),
        "benk": hist.get("points_on_bench"),
        "trekk": hist.get("event_transfers_cost") or 0,
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

    ferdig = sum(1 for f in kamper if f["finished"])
    live = sum(1 for f in kamper if f["started"] and not f["finished"])

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
        d.update(hent_lag(eid, gw_id, spillere))
        deltakere.append(d)

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

    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="bygg uansett (hopper over live-sjekk)")
    args = ap.parse_args()

    data = bygg()
    k = data["kamper"]
    status = "LIVE" if data["live"] else ("ferdig" if data["gw"]["ferdig"] else "venter")
    print(f"GW{data['gw']['id']} [{status}] - {k['ferdig']}/{k['totalt']} ferdig, {k['live']} paagaar")
    print(f"{len(data['deltakere'])} deltakere, leder: {data['deltakere'][0]['lagnavn']} "
          f"({data['deltakere'][0]['total']} p)")
    print(f"skrev {DIST / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
