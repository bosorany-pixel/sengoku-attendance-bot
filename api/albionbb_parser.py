"""
Parser for Albion BB guild attendance page.
Uses requests + BeautifulSoup only (no Selenium). Data is server-rendered in HTML.
All players are loaded from the first page's __NUXT_DATA__ payload (no pagination needed).
Results are cached for 24 hours; refetch only when cache is older than that.
"""
import json
import re
import time
from datetime import datetime, date, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

MORDOR_ATTENDANCE_URL = "https://europe.albionbb.com/guilds/nJTbhlRxTh2RAGMclSKk7A/attendance?minPlayers=20&start="
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
CACHE_TTL_SECONDS = 24 * 3600  # 24 hours

# Module-level cache: {"data": dict, "fetched_at": float}
_cache: dict[str, Any] | None = None


def _parse_short_number(s: str) -> float | int:
    """Parse values like '1.9k', '129.8m', '42', '864.6k' into numeric."""
    if not s or s.strip() == "":
        return 0
    s = s.strip().lower().replace(",", "")
    if s.endswith("k"):
        return float(s[:-1]) * 1_000
    if s.endswith("m"):
        return float(s[:-1]) * 1_000_000
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return 0


def fetch_attendance_html(url: str = MORDOR_ATTENDANCE_URL + (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")) -> str:
    """Fetch the guild attendance page HTML."""
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text


def _extract_nuxt_payload(html: str) -> list[Any] | None:
    """Extract and parse the __NUXT_DATA__ JSON array from the page."""
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NUXT_DATA__", "type": "application/json"})
    if not script or not script.string:
        return None
    try:
        return json.loads(script.string)
    except json.JSONDecodeError:
        return None


def _resolve_ref(payload: list[Any], idx: int, visited: set[int] | None = None) -> Any:
    """Resolve a Nuxt payload slot.

    Nuxt's `__NUXT_DATA__` payload is an array. Dict/list values often contain
    integers that reference another slot.

    Critical nuance for AlbionBB:
    Metric slots resolve to primitive ints (e.g. attendance=29). Those primitive
    ints are **real values**, not another reference.

    So we resolve exactly one hop (idx -> payload[idx]) and recursively resolve
    dict/list contents. If a slot contains an int, treat it as a literal.
    """
    if visited is None:
        visited = set()
    if idx in visited or idx < 0 or idx >= len(payload):
        return payload[idx] if 0 <= idx < len(payload) else None
    v = payload[idx]
    if isinstance(v, int):
        # Treat primitive ints as literal values.
        # Do NOT attempt int->slot chaining: it will misread real numbers like 29
        # as "payload[29]".
        return v
    if isinstance(v, dict):
        visited.add(idx)
        return {
            k: _resolve_ref(payload, x, visited)
            if isinstance(x, int) and 0 <= x < len(payload)
            else x
            for k, x in v.items()
        }
    if isinstance(v, list):
        visited.add(idx)
        return [
            _resolve_ref(payload, x, visited)
            if isinstance(x, int) and 0 <= x < len(payload)
            else x
            for x in v
        ]
    return v


def _parse_players_from_nuxt(html: str) -> list[dict[str, Any]] | None:
    """
    Extract all players from the __NUXT_DATA__ payload (single page has full list).
    Returns list of player dicts or None if extraction fails.
    """
    payload = _extract_nuxt_payload(html)
    if not payload or not isinstance(payload, list):
        return None
    # Find the list of player indices.
    # Nuxt contains many lists of ints; we score candidates by checking whether
    # their elements point to dicts that look like player rows.
    player_indices: list[int] | None = None
    best_score = -1
    for item in payload:
        if not (isinstance(item, list) and len(item) > 25 and all(isinstance(x, int) for x in item)):
            continue
        sample = item[: min(40, len(item))]
        score = 0
        for idx in sample:
            if not (0 <= idx < len(payload) and isinstance(payload[idx], dict)):
                continue
            d = payload[idx]
            if "name" in d and ("attendance" in d or "kills" in d or "avgIp" in d):
                score += 1
        if score > best_score:
            best_score = score
            player_indices = item
    if not player_indices:
        return None
    players: list[dict[str, Any]] = []
    for rank, idx in enumerate(player_indices, start=1):
        if idx < 0 or idx >= len(payload):
            continue
        obj = payload[idx]
        if not isinstance(obj, dict) or "name" not in obj:
            continue
        resolved = _resolve_ref(payload, idx)
        if not isinstance(resolved, dict):
            continue
        name = resolved.get("name")
        if not name or not isinstance(name, str):
            continue
        last_battle = resolved.get("lastBattle")
        if isinstance(last_battle, str) and "T" in last_battle:
            try:
                dt = datetime.fromisoformat(last_battle.replace("Z", "+00:00"))
                last_battle = dt.strftime("%B %d, %Y")
            except Exception:
                pass
        elif not isinstance(last_battle, str):
            last_battle = str(last_battle) if last_battle is not None else ""
        def num(x: Any) -> float | int:
            if x is None: return 0
            if isinstance(x, (int, float)): return x
            return 0
        players.append({
            "rank": rank,
            "name": name,
            "last_battle": last_battle,
            "attendance": int(num(resolved.get("attendance"))),
            "kills": int(num(resolved.get("kills"))),
            "deaths": int(num(resolved.get("deaths"))),
            "avg_ip": int(num(resolved.get("avgIp"))),
            "damage": num(resolved.get("damage")),
            "heal": num(resolved.get("heal")),
            "kill_fame": num(resolved.get("killFame")),
            "death_fame": num(resolved.get("deathFame")),
        })
    return players if players else None


def parse_stats(html: str) -> dict[str, Any]:
    """
    Parse guild attendance HTML into a structured dict matching the page stats.
    Returns the same data as the website: summary stats + players list.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Guild name: first h1 with class text-3xl (main title)
    guild_name = ""
    for h1 in soup.select("h1.text-3xl"):
        t = h1.get_text(strip=True)
        if t and t != "STATS":
            guild_name = t
            break

    # Summary stat cards: grid of cards with uppercase label and big number
    stats_labels = [
        "Total kills",
        "Total deaths",
        "Total damage",
        "Total heal",
        "Average attendance",
        "Average ip",
        "Total kill fame",
        "Total death fame",
    ]
    summary: dict[str, Any] = {}
    for card in soup.select("div.rounded-xl.border"):
        label_el = card.find(class_=re.compile(r"uppercase"))
        value_el = card.select_one(".text-center span")
        if label_el and value_el:
            label = label_el.get_text(strip=True)
            value_text = value_el.get_text(strip=True)
            if label in stats_labels:
                key = label.lower().replace(" ", "_")
                summary[key] = _parse_short_number(value_text)

    # Normalize keys to match common naming
    summary["total_kills"] = summary.get("total_kills", 0)
    summary["total_deaths"] = summary.get("total_deaths", 0)
    summary["total_damage"] = summary.get("total_damage", 0)
    summary["total_heal"] = summary.get("total_heal", 0)
    summary["average_attendance"] = int(summary.get("average_attendance", 0))
    summary["average_ip"] = int(summary.get("average_ip", 0))
    summary["total_kill_fame"] = summary.get("total_kill_fame", 0)
    summary["total_death_fame"] = summary.get("total_death_fame", 0)

    # Prefer all players from __NUXT_DATA__ (single page has full list)
    nuxt_players = _parse_players_from_nuxt(html)
    if nuxt_players:
        return _build_response(guild_name, summary, nuxt_players)

    # Fallback: players from first page table only
    players: list[dict[str, Any]] = []
    tbody = soup.select_one("table.table tbody")
    if not tbody:
        return _build_response(guild_name, summary, players)

    for tr in tbody.select("tr"):
        tds = tr.select("td")
        if len(tds) < 11:
            continue
        # n. | name | last battle | attend. | kills | deaths | avg ip | dmg | heal | kFame | dFame | [role columns...]
        rank_text = tds[0].get_text(strip=True).rstrip(".")
        name_el = tds[1].select_one("a")
        name = name_el.get_text(strip=True) if name_el else tds[1].get_text(strip=True)
        last_battle = tds[2].get_text(strip=True)
        attendance = tds[3].get_text(strip=True)
        kills = tds[4].get_text(strip=True)
        deaths = tds[5].get_text(strip=True)
        avg_ip = tds[6].get_text(strip=True)
        dmg = tds[7].get_text(strip=True)
        heal = tds[8].get_text(strip=True)
        k_fame = tds[9].get_text(strip=True)
        d_fame = tds[10].get_text(strip=True)

        try:
            rank = int(rank_text) if rank_text.isdigit() else 0
        except ValueError:
            rank = 0

        players.append({
            "rank": rank,
            "name": name,
            "last_battle": last_battle,
            "attendance": int(_parse_short_number(attendance)),
            "kills": int(_parse_short_number(kills)),
            "deaths": int(_parse_short_number(deaths)),
            "avg_ip": int(_parse_short_number(avg_ip)),
            "damage": int(_parse_short_number(dmg)),
            "heal": int(_parse_short_number(heal)),
            "kill_fame": int(_parse_short_number(k_fame)),
            "death_fame": int(_parse_short_number(d_fame)),
        })

    return _build_response(guild_name, summary, players)


def _build_response(
    guild_name: str,
    summary: dict[str, Any],
    players: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "guild_name": guild_name,
        "source": "https://europe.albionbb.com/",
        "summary": summary,
        "players_count": len(players),
        "players": players,
    }


def get_mordor_stats() -> dict[str, Any]:
    """
    Fetch and parse Mordor guild attendance; returns JSON-serializable dict.
    Uses cache: refetches from Albion BB only if last fetch is older than 24 hours.
    """
    global _cache
    now = time.time()
    if _cache is not None:
        age = now - _cache["fetched_at"]
        if age < CACHE_TTL_SECONDS:
            return _cache["data"]
    html = fetch_attendance_html()
    data = parse_stats(html)
    _cache = {"data": data, "fetched_at": now}
    return data
