"""Tynn klient mot FPL sitt aapne API. Ingen noekkel, ingen auth.

Alle endepunkter ligger under https://fantasy.premierleague.com/api/ og svarer JSON.
Varnish cacher 300 s foran, saa hyppigere henting enn det gir ingenting.
"""

import json
import time
import urllib.error
import urllib.request

BASE = "https://fantasy.premierleague.com/api"
LIGA_ID = 562901  # Norconsult Sarpsborg 26/27

_UA = "Mozilla/5.0 (hangaard.no FPL-tavle)"


_memo = {}


def _get(sti, forsok=4):
    """GET med enkel backoff. FPL kan gi sporadiske 5xx/SSL-brudd.

    Memoiseres per prosess: bor_bygge() og bygg() ber begge om bootstrap
    (1,5 MB) og fixtures, og det er ingen grunn til aa hente dem to ganger
    i samme kjoering.
    """
    if sti in _memo:
        return _memo[sti]
    url = f"{BASE}/{sti}"
    siste = None
    for n in range(forsok):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                _memo[sti] = json.load(r)
                return _memo[sti]
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            siste = e
            if n < forsok - 1:
                time.sleep(2 ** n)
    raise RuntimeError(f"ga opp {url} etter {forsok} forsok: {siste}")


def bootstrap():
    """Spillere, lag, gameweeks. ~1,5 MB, hentes en gang per kjoering."""
    return _get("bootstrap-static/")


def standings(liga_id=LIGA_ID):
    """Ligatabellen. 50 per side; vi er 9, saa en side holder lenge."""
    return _get(f"leagues-classic/{liga_id}/standings/")


def entry(entry_id):
    """Manager-info. Herfra henter vi player_first_name."""
    return _get(f"entry/{entry_id}/")


def picks(entry_id, gw):
    """Laget en manager stilte i en gitt GW. Tomt foer deadline."""
    return _get(f"entry/{entry_id}/event/{gw}/picks/")


def fixtures(gw=None):
    return _get("fixtures/" if gw is None else f"fixtures/?event={gw}")


def naavaerende_gw(bs):
    """Naavaerende GW, med fallback til neste hvis sesongen ikke har startet."""
    for e in bs["events"]:
        if e["is_current"]:
            return e
    for e in bs["events"]:
        if e["is_next"]:
            return e
    return bs["events"][0]
