import ctypes
import threading
from ctypes import wintypes
from dataclasses import dataclass
from functools import lru_cache
from struct import unpack_from
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

from utils.pointer_util import Pointers

# ============================================================
# Constantes WinAPI
# ============================================================
PAGE_GUARD = 0x100
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40

MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
MEM_MAPPED = 0x40000
MEM_IMAGE = 0x1000000


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", wintypes.LPVOID),
        ("AllocationBase", wintypes.LPVOID),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
VirtualQueryEx = kernel32.VirtualQueryEx
VirtualQueryEx.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    ctypes.POINTER(MEMORY_BASIC_INFORMATION),
    ctypes.c_size_t,
]
VirtualQueryEx.restype = ctypes.c_size_t


# ============================================================
# Modelos / utilitários
# ============================================================

@dataclass(frozen=True)
class PersonagemEncontrado:
    """Representa um resultado encontrado no scan."""
    nome: Optional[str]
    x: int
    y: int
    addr_padrao: int
    addr_nome: Optional[int]

    def to_dict(self) -> dict:
        return {
            "nome": self.nome,
            "x": self.x,
            "y": self.y,
            "addr_padrao": hex(self.addr_padrao),
            "addr_nome": hex(self.addr_nome) if self.addr_nome is not None else None,
        }


class FiltroIgnorarNomes:
    """
    Filtro de nomes a ignorar.
    - Exato por bytes (muito rápido)
    - Parcial por string (mais lento, use com cuidado)
    - Reverse-contains opcional (para casos truncados: 'ath Tree' em 'Death Tree')
    """
    def __init__(self, nomes_exatos: Sequence[str]) -> None:
        self._ignorados_str: Set[str] = set(nomes_exatos)
        self._ignorados_bytes: Set[bytes] = {s.encode("ascii", errors="ignore") for s in self._ignorados_str}
        self._ignorados_bytes_lower: Set[bytes] = {b.lower() for b in self._ignorados_bytes}

        # Regras parciais (evite listas enormes)
        self._ignorados_parciais_lower: Tuple[str, ...] = ("data\\interf",)

        # Reverse-contains só para truncados (poucos termos!)
        self._reverse_para_truncados_lower: Tuple[str, ...] = (
            # exemplo: "death tree",
        )

    def adicionar(self, nome: Union[str, bytes]) -> None:
        if not nome:
            return
        if isinstance(nome, bytes):
            b = nome.split(b"\x00", 1)[0]
            s = b.decode("ascii", errors="ignore")
        else:
            s = str(nome)
            b = s.encode("ascii", errors="ignore")

        self._ignorados_str.add(s)
        self._ignorados_bytes.add(b)
        self._ignorados_bytes_lower.add(b.lower())

    def ignorar_por_bytes_exato(self, raw0: bytes) -> bool:
        return raw0.lower() in self._ignorados_bytes_lower

    def ignorar_por_string(self, nome: str) -> bool:
        if not nome:
            return True
        nome_low = nome.lower()

        # parcial (poucos)
        for p in self._ignorados_parciais_lower:
            if p in nome_low:
                return True

        # reverse-contains só quando truncado (heurística simples)
        if len(nome_low) <= 8:
            for ref in self._reverse_para_truncados_lower:
                if nome_low in ref:
                    return True

        # compatibilidade com a regra antiga: ignore_nome in nome OR nome in ignore_nome
        # (mais caro; então mantém somente no conjunto base)
        for ign in self._ignorados_str:
            if ign and (ign in nome or nome in ign):
                return True

        return False


class SanitizadorAscii:
    """Sanitiza bytes para ASCII imprimível com alta performance (translate em C)."""
    def __init__(self) -> None:
        self._tabela = bytes((b if 32 <= b <= 126 else 0) for b in range(256))

    def limpar(self, raw: bytes) -> bytes:
        """
        - corta no primeiro NUL
        - troca bytes não-imprimíveis por 0
        - remove zeros e espaços laterais
        """
        if not raw:
            return b""
        raw0 = raw.split(b"\x00", 1)[0]
        if not raw0:
            return b""
        clean = raw0.translate(self._tabela)
        clean = clean.replace(b"\x00", b"").strip()
        return clean


class IteradorRegioesMemoria:
    """Itera regiões do processo via VirtualQueryEx."""
    def iterar(self, process_handle) -> Iterable[Tuple[int, int, MEMORY_BASIC_INFORMATION]]:
        addr = 0
        mbi = MEMORY_BASIC_INFORMATION()
        sizeof_mbi = ctypes.sizeof(mbi)

        while True:
            got = VirtualQueryEx(process_handle, ctypes.c_void_p(addr), ctypes.byref(mbi), sizeof_mbi)
            if not got:
                break

            base = ctypes.cast(mbi.BaseAddress, ctypes.c_void_p).value or 0
            size = int(mbi.RegionSize)
            if size <= 0:
                break

            yield base, size, MEMORY_BASIC_INFORMATION.from_buffer_copy(mbi)

            next_addr = base + size
            if next_addr <= addr:
                break
            addr = next_addr


class CacheRangeFixo:
    """Cache global (por classe) de ranges fixos por (pid, padrao)."""
    _ranges: Dict[Tuple[int, bytes], Tuple[int, int]] = {}
    _lock = threading.Lock()

    @classmethod
    def get(cls, pid: int, padrao: bytes) -> Optional[Tuple[int, int]]:
        with cls._lock:
            return cls._ranges.get((pid, padrao))

    @classmethod
    def set(cls, pid: int, padrao: bytes, ini: int, fim: int) -> None:
        with cls._lock:
            cls._ranges[(pid, padrao)] = (ini, fim)

    @classmethod
    def pop(cls, pid: int, padrao: bytes) -> None:
        with cls._lock:
            cls._ranges.pop((pid, padrao), None)


class ValidadorRegiao:
    """Verifica se um endereço ainda está em região COMMIT e legível."""
    def __init__(self, pointer: Pointers) -> None:
        self._pointer = pointer

    def endereco_legivel(self, base: int) -> bool:
        mbi = MEMORY_BASIC_INFORMATION()
        got = VirtualQueryEx(
            self._pointer.pm.process_handle,
            ctypes.c_void_p(base),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi),
        )
        if not got:
            return False

        if mbi.State != MEM_COMMIT:
            return False
        if mbi.Type not in (MEM_PRIVATE, MEM_MAPPED, MEM_IMAGE):
            return False

        p = int(mbi.Protect)
        if p & PAGE_GUARD:
            return False
        if not (p & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE)):
            return False

        region_base = ctypes.cast(mbi.BaseAddress, ctypes.c_void_p).value or 0
        region_size = int(mbi.RegionSize)
        return region_base <= base < region_base + region_size


class OrdemMSB:
    _BASE: Dict[str, Tuple[int, ...]] = {
        "0-9A-Z": tuple(range(0x00, 0x24)),
        "0-9": tuple(range(0x00, 0x0A)),
        "A-Z": tuple(range(0x0A, 0x24)),
        "A-F": tuple(range(0x0A, 0x10)),
    }

    @staticmethod
    @lru_cache(maxsize=128)
    def construir(charset: str = "0-9A-Z", hints: Tuple[int, ...] = ()) -> Tuple[int, ...]:
        base = OrdemMSB._BASE.get(charset)
        if base is None:
            seq: List[int] = []
            if "0-9" in charset:
                seq.extend(range(0x00, 0x0A))
            if "A-Z" in charset:
                seq.extend(range(0x0A, 0x24))
            base = tuple(seq)

        if not hints:
            return base

        base_set = set(base)
        seen = [False] * 256
        prefix: List[int] = []
        for h in hints:
            v = int(h) & 0xFF
            if v in base_set and not seen[v]:
                seen[v] = True
                prefix.append(v)

        if not prefix:
            return base

        tail = [x for x in base if not seen[x]]
        return tuple(prefix + tail)


class EncontradorRangePorMSB:
    """
    Encontra um range [ini, fim] dentro de regiões MEM_PRIVATE COMMIT, usando um padrao (bytes)
    e restrições de MSB (do low32 do endereço).
    """
    def __init__(self, pointer: Pointers) -> None:
        self._pointer = pointer
        self._iter = IteradorRegioesMemoria()

        self._cache_lock = threading.Lock()
        self._cache: Dict[Tuple, Tuple[Optional[int], Optional[int]]] = {}

    def achar_cached(
        self,
        *,
        padrao: bytes,
        bloco_leitura: int,
        margem: int,
        exigir_rw: bool,
        msb: int,
        require_region_msb: bool,
        use_msb_band_hint: bool,
        force_refresh: bool,
    ) -> Tuple[Optional[int], Optional[int]]:
        pid = getattr(self._pointer.pm, "process_id", None)
        key = (pid, msb, padrao, exigir_rw, bloco_leitura, margem, require_region_msb, use_msb_band_hint)

        if not force_refresh:
            with self._cache_lock:
                hit = self._cache.get(key)
                if hit:
                    return hit

        ini, fim = self.achar(
            padrao=padrao,
            bloco_leitura=bloco_leitura,
            margem=margem,
            exigir_rw=exigir_rw,
            msb=msb,
            require_region_msb=require_region_msb,
            use_msb_band_hint=use_msb_band_hint,
        )

        with self._cache_lock:
            self._cache[key] = (ini, fim)

        return ini, fim

    def achar(
        self,
        *,
        padrao: bytes,
        bloco_leitura: int,
        margem: int,
        exigir_rw: bool,
        msb: int,
        require_region_msb: bool,
        use_msb_band_hint: bool,
    ) -> Tuple[Optional[int], Optional[int]]:

        def is_rw(protect: int) -> bool:
            if protect & PAGE_GUARD:
                return False
            return bool(protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE))

        def low32(addr: int) -> int:
            return int(addr) & 0xFFFFFFFF

        def has_msb(addr: int, wanted_msb: int) -> bool:
            return ((low32(addr) >> 24) & 0xFF) == (wanted_msb & 0xFF)

        def region_intersects_msb_band(region_start: int, size: int, wanted_msb: int) -> bool:
            if size <= 0:
                return False
            region_end = region_start + size - 1
            band_lo = (wanted_msb & 0xFF) << 24
            band_hi = ((wanted_msb + 1) & 0xFF) << 24
            probes = (region_start, region_start + (size // 2), region_end)
            for p in probes:
                l32 = low32(p)
                if band_lo <= l32 < band_hi:
                    return True
            return False

        carry_len = max(0, len(padrao) - 1)

        for region_start, size, mbi in self._iter.iterar(self._pointer.pm.process_handle):
            if mbi.State != MEM_COMMIT:
                continue
            if mbi.Type != MEM_PRIVATE:
                continue
            if exigir_rw and not is_rw(int(mbi.Protect)):
                continue

            if require_region_msb:
                if not has_msb(region_start, msb):
                    continue
            else:
                if use_msb_band_hint and not region_intersects_msb_band(region_start, size, msb):
                    continue

            region_end = region_start + size
            addr = region_start
            prev_tail = b""

            first_hit: Optional[int] = None
            last_hit: Optional[int] = None
            hits_count = 0

            while addr < region_end:
                tam = min(bloco_leitura, region_end - addr)
                try:
                    buf = self._pointer.pm.read_bytes(addr, tam)
                except Exception:
                    addr += 0x1000
                    prev_tail = b""
                    continue

                scan_base = addr - len(prev_tail)
                scan_buf = (prev_tail + buf) if prev_tail else buf

                i = 0
                while True:
                    pos = scan_buf.find(padrao, i)
                    if pos == -1:
                        break
                    i = pos + 1
                    hit = scan_base + pos

                    if not has_msb(hit, msb):
                        continue

                    if first_hit is None:
                        first_hit = hit
                    last_hit = hit
                    hits_count += 1

                prev_tail = scan_buf[-carry_len:] if carry_len and len(scan_buf) >= carry_len else b""
                addr += tam

            if hits_count > 0 and first_hit is not None and last_hit is not None:
                base_inicio = max(first_hit - margem, 0)
                base_fim = last_hit + margem
                return base_inicio, base_fim

        return None, None


class ScannerPersonagens:
    """Faz o scan dentro de um range e extrai (nome, x, y)."""
    def __init__(
        self,
        pointer: Pointers,
        filtro: FiltroIgnorarNomes,
        sanitizador: SanitizadorAscii,
    ) -> None:
        self._pointer = pointer
        self._filtro = filtro
        self._san = sanitizador

    def scan_range(
        self,
        *,
        base_inicio: int,
        base_fim: int,
        padrao: bytes,
        bloco_leitura: int,
        name_delta: int,
        name_max: int,
        xy_max: int,
    ) -> List[PersonagemEncontrado]:
        need_before = 8
        carry_len = need_before + len(padrao) - 1

        resultados: List[PersonagemEncontrado] = []
        vistos: Set[Tuple[int, int, int]] = set()

        addr = base_inicio
        prev_tail = b""

        while addr < base_fim:
            tam = min(bloco_leitura, base_fim - addr)
            try:
                buf = self._pointer.pm.read_bytes(addr, tam)
            except Exception:
                addr += 0x1000
                prev_tail = b""
                continue

            scan_base = addr - len(prev_tail)
            scan_buf = prev_tail + buf

            i = 0
            while True:
                pos = scan_buf.find(padrao, i)
                if pos == -1:
                    break
                i = pos + 1

                if pos < need_before:
                    continue

                addr_padrao = scan_base + pos

                # Otimização: ler x/y direto do scan_buf (sem read_ushort)
                try:
                    y = unpack_from("<H", scan_buf, pos - 8)[0]
                    x = unpack_from("<H", scan_buf, pos - 4)[0]
                except Exception:
                    continue

                if not (0 < x < xy_max and 0 < y < xy_max):
                    continue

                addr_nome = addr_padrao - name_delta

                # Nome: tentar ler do scan_buf (zero syscall) quando possível
                raw_nome: Optional[bytes] = None
                idx_nome = addr_nome - scan_base
                if 0 <= idx_nome <= (len(scan_buf) - name_max):
                    raw_nome = scan_buf[idx_nome: idx_nome + name_max]
                else:
                    try:
                        raw_nome = self._pointer.pm.read_bytes(addr_nome, name_max)
                    except Exception:
                        raw_nome = None

                nome: Optional[str] = None

                if raw_nome:
                    clean_b = self._san.limpar(raw_nome)
                    if clean_b:
                        if self._filtro.ignorar_por_bytes_exato(clean_b):
                            continue

                        try:
                            cand = clean_b.decode("ascii", errors="ignore")
                        except Exception:
                            cand = ""

                        if cand and not self._filtro.ignorar_por_string(cand):
                            nome = cand

                # fallback: procura texto antes do padrão
                if not nome:
                    try:
                        pre_ini = max(base_inicio, addr_nome)
                        pre_len = min(64, addr_padrao - pre_ini)
                        if pre_len > 0:
                            pre = self._pointer.pm.read_bytes(pre_ini, pre_len)
                            clean_pre = self._san.limpar(pre)
                            if 3 <= len(clean_pre) <= name_max:
                                if self._filtro.ignorar_por_bytes_exato(clean_pre):
                                    continue
                                cand = clean_pre.decode("ascii", errors="ignore")
                                if cand and not self._filtro.ignorar_por_string(cand):
                                    nome = cand
                    except Exception:
                        pass

                chave = (addr_padrao, x, y)
                if chave in vistos:
                    continue
                vistos.add(chave)

                resultados.append(
                    PersonagemEncontrado(
                        nome=nome,
                        x=x,
                        y=y,
                        addr_padrao=addr_padrao,
                        addr_nome=addr_nome if nome is not None else None,
                    )
                )

            prev_tail = scan_buf[-carry_len:] if len(scan_buf) >= carry_len else scan_buf
            addr += tam

        return resultados


class OrdenadorProximos:
    """Filtra e ordena resultados próximos às coordenadas atuais do personagem."""
    def __init__(self, pointer: Pointers) -> None:
        self._pointer = pointer

    def ordenar(
        self,
        resultados: Sequence[Union[dict, tuple]],
        *,
        limite: Optional[int] = None,
        incluir_dist: bool = True,
        max_delta: int = 10,
    ) -> List[dict]:
        x0 = self._pointer.get_cood_x()
        y0 = self._pointer.get_cood_y()
        if x0 is None or y0 is None:
            print("[WARN] Coordenadas atuais indisponíveis.")
            return []

        proximos: List[dict] = []

        for item in resultados:
            try:
                if isinstance(item, dict):
                    x = int(item.get("x"))
                    y = int(item.get("y"))
                    nome = item.get("nome")
                    addr_raw = item.get("addr_padrao") or item.get("addr_nome") or item.get("addr") or item.get("address")
                else:
                    addr_raw, x, y = item[0], int(item[1]), int(item[2])
                    nome = None
            except Exception:
                continue

            dx = x - x0
            dy = y - y0
            if abs(dx) > max_delta or abs(dy) > max_delta:
                continue

            dist = abs(dx) + abs(dy)

            sort_addr_val = 0
            if addr_raw is not None:
                try:
                    if isinstance(addr_raw, int):
                        sort_addr_val = addr_raw
                    else:
                        s = str(addr_raw).strip()
                        sort_addr_val = int(s, 16) if s.lower().startswith("0x") else int(s)
                except Exception:
                    sort_addr_val = abs(hash(addr_raw)) & 0x7FFFFFFF

            proximos.append(
                {
                    "x": x,
                    "y": y,
                    "dist": dist,
                    "nome": nome,
                    "_sort_addr_val": sort_addr_val,
                }
            )

        proximos.sort(key=lambda d: (d["dist"], d["_sort_addr_val"]))
        if limite is not None:
            proximos = proximos[:limite]

        saida: List[dict] = []
        for d in proximos:
            out = {"x": d["x"], "y": d["y"]}
            if incluir_dist:
                out["dist"] = d["dist"]
            if d.get("nome") is not None:
                out["nome"] = d["nome"]
            saida.append(out)
        return saida


# ============================================================
# Serviço principal (API compatível)
# ============================================================

class BuscarPersonagemProximoService:
    """
    Serviço refatorado (substitui BuscarPersoangemProximoService),
    mas mantém métodos com nomes antigos por compatibilidade.
    """

    MOBS_IGNORAR: Set[str] = {
        "Soldier de Alexi", "Guard Lancer", "Soldier de iorii", "Marlon",
        "Mutant", "Bloody Wolf", "Iron Wheel", "Cursed King", "Tantalos", "Hero Mutant", "Beam Knight",
        "Death Beam Knigh",
        "Alquamos", "Queen Rainier", "Drakan", "Alpha Crust", "Phantom Knight", "Great Drakan", "Metal Balrog",
        "Omega Wing", "Phoenix of Darkn",
        "Death Tree", "Forest Orc", "Death Rider", "Guard Archer", "Blue Golem", "Hell Maine", "Witch Queen",
        "Splinter Wolf", "Iron Rider", "Satyros", "Red Knight", "Kentauros", "Gigantis", "Berserker", "Twin Tale",
        "Persona", "Canon Trap", "Dreadfear",
        "Hero Mutant", "Lizard Warrior", "Rogue Centurion", "Death Angel", "Sea Worm", "Necron",
        "Death Centurion", "Schriker", "Blood Soldier", "Aegis",
        "data\\interf",
    }

    def __init__(self) -> None:
        self.pointer = Pointers()

        self._san = SanitizadorAscii()
        self._filtro = FiltroIgnorarNomes(self.MOBS_IGNORAR)

        try:
            myname = self.pointer.get_nome_char()
            if myname:
                self._filtro.adicionar(myname)
        except Exception:
            pass

        self._validador_regiao = ValidadorRegiao(self.pointer)
        self._finder_range = EncontradorRangePorMSB(self.pointer)
        self._scanner = ScannerPersonagens(self.pointer, self._filtro, self._san)
        self._ordenador = OrdenadorProximos(self.pointer)

        self._msb_result_cache: Dict[Tuple[int, int], Tuple[int, int]] = {}
        self._msb_hit_order: Dict[int, List[int]] = {}

    def listar_nomes_e_coords_por_padrao(
        self,
        padrao: bytes = b"\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF",
        bloco_leitura: int = 0x40000,
        name_delta: int = 0x74,
        name_max: int = 16,
        xy_max: int = 4096,
        start_hints: Sequence[int] = (0x0E, 0x0F, 0x0A, 0x08, 0x0B),
        force_refresh: bool = False,
        mobs_ignorar: Optional[Sequence[Union[str, bytes]]] = None,
    ) -> List[dict]:

        if mobs_ignorar:
            for s in mobs_ignorar:
                self._filtro.adicionar(s)

        pid = int(getattr(self.pointer.pm, "process_id", 0) or 0)

        if not force_refresh:
            fixed = CacheRangeFixo.get(pid, padrao)
            if fixed:
                f_ini, f_fim = fixed
                if f_ini < f_fim and self._validador_regiao.endereco_legivel(f_ini):
                    res = self._scanner.scan_range(
                        base_inicio=f_ini,
                        base_fim=f_fim,
                        padrao=padrao,
                        bloco_leitura=bloco_leitura,
                        name_delta=name_delta,
                        name_max=name_max,
                        xy_max=xy_max,
                    )
                    if res:
                        if res[0].nome == "data\\interf":
                            print("[SCAN] Range fixo retornou apenas 'data\\\\interf', descartando cache fixo...")
                            CacheRangeFixo.pop(pid, padrao)
                        else:
                            return [r.to_dict() for r in res]
                else:
                    CacheRangeFixo.pop(pid, padrao)

        msb_order = OrdemMSB.construir("0-9A-Z", tuple(start_hints))
        msb_order_set = set(msb_order)

        hints_clean: List[int] = []
        seen = set()
        for h in start_hints:
            v = int(h) & 0xFF
            if v in msb_order_set and v not in seen:
                hints_clean.append(v)
                seen.add(v)

        for msb in hints_clean:
            rng = self._msb_result_cache.get((pid, msb))
            if rng:
                b0, b1 = rng
                if b0 < b1:
                    res = self._scanner.scan_range(
                        base_inicio=b0,
                        base_fim=b1,
                        padrao=padrao,
                        bloco_leitura=bloco_leitura,
                        name_delta=name_delta,
                        name_max=name_max,
                        xy_max=xy_max,
                    )
                    if res:
                        print(f"[SCAN] Cache hit MSB={hex(msb)} (hints) ({len(res)} resultados)")
                        return [r.to_dict() for r in res]

            for margem, req_msb, hint in (
                (0x800, True, True),
                (0x1000, False, True),
                (0x2000, False, False),
            ):
                b0, b1 = self._finder_range.achar_cached(
                    padrao=padrao,
                    bloco_leitura=bloco_leitura,
                    margem=margem,
                    exigir_rw=True,
                    msb=msb,
                    require_region_msb=req_msb,
                    use_msb_band_hint=hint,
                    force_refresh=force_refresh,
                )
                if b0 and b1 and b0 < b1:
                    res = self._scanner.scan_range(
                        base_inicio=b0,
                        base_fim=b1,
                        padrao=padrao,
                        bloco_leitura=bloco_leitura,
                        name_delta=name_delta,
                        name_max=name_max,
                        xy_max=xy_max,
                    )
                    if res:
                        self._msb_result_cache[(pid, msb)] = (b0, b1)
                        hits = self._msb_hit_order.get(pid, [])
                        self._msb_hit_order[pid] = [msb] + [m for m in hits if m != msb]
                        CacheRangeFixo.set(pid, padrao, b0, b1)
                        print(f"[SCAN] Encontrado (hints) MSB={hex(msb)} base={hex(b0)}..{hex(b1)} ({len(res)} resultados)")
                        return [r.to_dict() for r in res]

        hits = self._msb_hit_order.get(pid, [])
        excluded = set(hints_clean)
        ordered = list(hits) + [m for m in msb_order if m not in excluded and m not in hits]

        consecutive_misses = 0
        MAX_MISSES = 3

        for msb in ordered:
            rng = self._msb_result_cache.get((pid, msb))
            if rng:
                b0, b1 = rng
                if b0 < b1:
                    res = self._scanner.scan_range(
                        base_inicio=b0,
                        base_fim=b1,
                        padrao=padrao,
                        bloco_leitura=bloco_leitura,
                        name_delta=name_delta,
                        name_max=name_max,
                        xy_max=xy_max,
                    )
                    if res:
                        print(f"[SCAN] Cache hit MSB={hex(msb)} (resto) ({len(res)} resultados)")
                        return [r.to_dict() for r in res]

                consecutive_misses += 1
                if consecutive_misses >= MAX_MISSES:
                    print(f"[SCAN] Abortado após {MAX_MISSES} misses consecutivos (resto)")
                    break
                continue

            found_here = False
            for margem, req_msb, hint in (
                (0x800, True, True),
                (0x1000, False, True),
                (0x2000, False, False),
            ):
                b0, b1 = self._finder_range.achar_cached(
                    padrao=padrao,
                    bloco_leitura=bloco_leitura,
                    margem=margem,
                    exigir_rw=True,
                    msb=msb,
                    require_region_msb=req_msb,
                    use_msb_band_hint=hint,
                    force_refresh=force_refresh,
                )
                if b0 and b1 and b0 < b1:
                    res = self._scanner.scan_range(
                        base_inicio=b0,
                        base_fim=b1,
                        padrao=padrao,
                        bloco_leitura=bloco_leitura,
                        name_delta=name_delta,
                        name_max=name_max,
                        xy_max=xy_max,
                    )
                    if res:
                        self._msb_result_cache[(pid, msb)] = (b0, b1)
                        self._msb_hit_order[pid] = [msb] + [m for m in hits if m != msb]
                        CacheRangeFixo.set(pid, padrao, b0, b1)
                        print(f"[SCAN] Encontrado (resto) MSB={hex(msb)} base={hex(b0)}..{hex(b1)} ({len(res)} resultados)")
                        return [r.to_dict() for r in res]

                    found_here = True

            if found_here:
                consecutive_misses = 0
            else:
                consecutive_misses += 1
                if consecutive_misses >= MAX_MISSES:
                    print(f"[SCAN] Abortado após {MAX_MISSES} misses consecutivos (resto)")
                    break

        print("[SCAN] Nenhum resultado.")
        return []

    def ordenar_proximos(
        self,
        resultados: List,
        limite: Optional[int] = None,
        incluir_dist: bool = True
    ) -> List[dict]:
        return self._ordenador.ordenar(resultados, limite=limite, incluir_dist=incluir_dist)


class BuscarPersoangemProximoService(BuscarPersonagemProximoService):
    """Alias compatível com o nome antigo (typo)."""
    pass
