#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Raspador que junta todos os personagens das guilds em um único JSON:
{
  "data_hora": "...",
  "Personagem": [...]
}
Atualiza apenas se a última versão tiver mais de 12h.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime, timedelta

BASE_URL = "https://www.mucabrasil.com.br/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MuCA-scraper/1.3)"}
TIMEOUT = 15
DELAY = 0.5

GUILD_NAMES = [
    "ToHeLL_", "ToHeLL2", "ToHeLL3", "ToHeLL4", "ToHeLL5",
    "ToHeLL10", "ToHeLL6", "ToHeLL7", "ToHeLL8_", "ToHeLL9",
]
PAGES = [1, 2]
OUTPUT_FILE = "/data/personagens.json"


def precisa_atualizar() -> bool:
    """Verifica se o arquivo JSON existe e se tem mais de 12h."""
    if not os.path.exists(OUTPUT_FILE):
        return True
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        ultima_data = datetime.fromisoformat(data.get("data_hora"))
        if datetime.now() - ultima_data > timedelta(hours=12):
            return True
        print("[INFO] JSON atualizado há menos de 12h, sem necessidade de atualização.")
        return False
    except Exception:
        return True


def fetch_html(guild: str, page: int) -> str | None:
    params = {"go": "guild", "n": guild, "p": page}
    try:
        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        return r.text
    except requests.RequestException:
        return None


def find_header_row_and_col_idx(table):
    rows = table.find_all("tr")
    for h_idx, tr in enumerate(rows):
        headers = [c.get_text(strip=True).lower().replace("\xa0", " ") for c in tr.find_all(["th", "td"])]
        if any("personagem" in h for h in headers):
            for i, h in enumerate(headers):
                if "personagem" in h:
                    return h_idx, i
    return None, None


def coletar_personagens(guild: str, page: int) -> list[str]:
    html = fetch_html(guild, page)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    nomes = []
    for t in tables:
        header_row_idx, col_idx = find_header_row_and_col_idx(t)
        if col_idx is None:
            continue
        rows = t.find_all("tr")
        for tr in rows[header_row_idx + 1:]:
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            if col_idx < len(cells):
                cell = cells[col_idx]
                a = cell.find("a")
                name = (a.get_text(strip=True) if a and a.get_text(strip=True)
                        else cell.get_text(separator=" ", strip=True))
                name = name.replace("\xa0", " ").strip()
                if name:
                    nomes.append(name)
    return nomes


def main():
    if not precisa_atualizar():
        return

    todos = []
    for guild in GUILD_NAMES:
        for p in PAGES:
            nomes = coletar_personagens(guild, p)
            todos.extend(nomes)
            time.sleep(DELAY)

    # remover duplicados preservando ordem
    seen = set()
    personagens = []
    for n in todos:
        if n not in seen:
            personagens.append(n)
            seen.add(n)

    data = {
        "data_hora": datetime.now().isoformat(timespec="seconds"),
        "Personagem": personagens
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] JSON atualizado com {len(personagens)} personagens em {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
