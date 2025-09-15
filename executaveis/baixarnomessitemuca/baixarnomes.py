import time
import re
from typing import List, Optional, Iterator
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mucabrasil.com.br"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HallFamaScraper/2.0"

CLASSES = {
    "Soul Master",
    "Blade Knight",
    "Muse Elf",
    "Magic Gladiator",
    "Dark Lord",
}

MAPA_CLASSE_C = {
    "Todos": 0,
    "Soul Master": 1,
    "Blade Knight": 2,
    "Muse Elf": 3,
    "Magic Gladiator": 4,
    "Dark Lord": 5,
}

def _to_c(classe: Optional[str | int]) -> int:
    if classe is None:
        return 0
    if isinstance(classe, int):
        return classe
    return MAPA_CLASSE_C.get(classe, 0)

def _req(url: str, tentativas: int = 3, pausa: float = 0.6) -> BeautifulSoup:
    ultimo = None
    for _ in range(tentativas):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
            r.encoding = r.apparent_encoding or r.encoding or "utf-8"
            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")
            ultimo = RuntimeError(f"HTTP {r.status_code}")
        except Exception as e:
            ultimo = e
        time.sleep(pausa)
    raise RuntimeError(f"Falha ao requisitar {url}: {ultimo}")

def _is_int_token(t: str) -> bool:
    return bool(re.fullmatch(r"\d+", t))

def _tokens_tabela(soup: BeautifulSoup) -> List[str]:
    tokens: List[str] = []
    coletando = False
    for t in soup.stripped_strings:
        if t == "N":  # início da grade
            coletando = True
            continue
        if not coletando:
            continue
        if t.startswith("<< Anterior") or t.startswith("Painel"):
            break
        tokens.append(t)

    # remover cabeçalho textual, se vier linearizado
    cab = ["Personagem", "Classe", "Level", "Guild", "Resets"]
    if tokens[:5] == cab:
        tokens = tokens[5:]
    return tokens

def _iter_linhas(tokens: List[str]) -> Iterator[tuple[int, str, str, int, str, int]]:
    """
    Reconstrói linhas no formato:
    (posicao, personagem, classe, level, guild, resets)
    Tolerante a 'Guild' vazia (ausente).
    """
    i = 0
    n = len(tokens)
    while i < n:
        # posicao
        if i >= n or not _is_int_token(tokens[i]):
            break
        posicao = int(tokens[i]); i += 1

        # personagem
        if i >= n:
            break
        personagem = tokens[i]; i += 1

        # classe (pode ter espaço; consome até bater uma das CLASSES)
        # tenta 2 tokens (p.ex. "Blade"+"Knight") ou 1 (se algum dia mudarem)
        if i >= n:
            break
        classe = tokens[i]
        if i + 1 < n and f"{classe} {tokens[i+1]}" in CLASSES:
            classe = f"{classe} {tokens[i+1]}"
            i += 2
        elif classe in CLASSES:
            i += 1
        else:
            # fallback: tenta juntar até formar uma classe conhecida (máx. 3 tokens)
            juntou = False
            for extra in (1, 2):
                if i + extra < n:
                    possivel = " ".join(tokens[i-1:i-1+extra+1])  # inclui o já lido
                    if possivel in CLASSES:
                        classe = possivel
                        i = i - 1 + extra + 1
                        juntou = True
                        break
            if not juntou and classe not in CLASSES:
                # classe desconhecida → aborta linha
                break

        # level
        if i >= n or not _is_int_token(tokens[i]):
            break
        level = int(tokens[i]); i += 1

        # guild (pode estar vazia → nesse caso o próximo token já é resets)
        guild = ""
        if i < n and not _is_int_token(tokens[i]):
            guild = tokens[i].replace("\xa0", " ").strip()
            i += 1

        # resets
        if i >= n or not _is_int_token(tokens[i]):
            break
        resets = int(tokens[i]); i += 1

        yield (posicao, personagem, classe, level, guild, resets)

def _tem_proxima_pagina(soup: BeautifulSoup) -> bool:
    link = soup.find("a", string=re.compile(r"Próxima\s*>>"))
    if not link:
        return False
    href = link.get("href", "").strip()
    return href and len(href) > 1

def personagens_sem_guild_hall_fama_ano(
    ano: int,
    classe: str | int = "Todos",
    pausa_paginas: float = 0.4,
    limite_paginas: Optional[int] = None,
) -> List[str]:
    """
    Varre TODAS as páginas do Hall da Fama para o ano/classe e retorna
    apenas os nomes (strings) dos personagens sem guild.
    """
    c = _to_c(classe)
    pagina = 1
    lidas = 0
    nomes: List[str] = []

    while True:
        url = f"{BASE_URL}/?go=hallfama&y={ano}&p={pagina}&c={c}"
        soup = _req(url)
        tokens = _tokens_tabela(soup)

        houve_linha = False
        for (_pos, personagem, _classe, _level, guild, _resets) in _iter_linhas(tokens):
            houve_linha = True
            if not guild.strip():
                nomes.append(personagem.strip())

        lidas += 1
        if (limite_paginas and lidas >= limite_paginas) or not _tem_proxima_pagina(soup) or not houve_linha:
            break

        pagina += 1
        time.sleep(pausa_paginas)

    return nomes

# ---------- exemplo de uso ----------
if __name__ == "__main__":
    # Ano 2025, todas as classes, varrendo todas as páginas
    sem_guild = personagens_sem_guild_hall_fama_ano(ano=2025, classe="Todos")
    print(f"Total sem guild (2025): {len(sem_guild)}")
    print(sem_guild[:30])  # amostra
