import ctypes
import threading
import time
from ctypes import wintypes
from functools import lru_cache
from typing import Optional, Tuple, Iterable, Dict, List, Set

# ==== Constantes WinAPI (mantenha no topo do arquivo) ====
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
    wintypes.HANDLE, wintypes.LPCVOID,
    ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t
]
VirtualQueryEx.restype = ctypes.c_size_t


class BuscarPersoangemProximoService:
    # ---- Lista base de MOBS a ignorar (match EXATO) ----
    MOBS_IGNORAR: Set[str] = {
        #NPC
        'Soldier de Alexi',
        # TARKAN
        'Mutant', 'Bloody Wolf', 'Iron Wheel', 'Cursed King', 'Tantalos', 'Hero Mutant', 'Beam Knight',
        'Death Beam Knigh',
        # ICARUS
        'Alquamos', 'Queen Rainier', 'Drakan', 'Alpha Crust', 'Phantom Knight', 'Great Drakan', 'Metal Balrog',
        'Omega Wing', 'Phoenix of Darkn',
        # AIDA
        'Death Tree', 'Forest Orc', 'Death Rider', 'Guard Archer', 'Blue Golem', 'Hell Maine', 'Witch Queen',
        # KALIMA
        'Hero Mutant', 'Lizard Warrior', 'Rogue Centurion', 'Death Angel', 'Sea Worm', 'Necron', 'Death Centurion',
        'Schriker', 'Blood Soldier', 'Aegis'
    }

    # ---- Ordens MSB pré-calculadas ----
    _MSB_BASE_ORDERS: Dict[str, Tuple[int, ...]] = {
        "0-9A-Z": tuple(range(0x00, 0x24)),  # 0..35 (0x00..0x23)
        "0-9":    tuple(range(0x00, 0x0A)),  # 0..9
        "A-Z":    tuple(range(0x0A, 0x24)),  # 10..35
        "A-F":    tuple(range(0x0A, 0x10)),  # 10..15
    }

    # ---- Caches globais por classe ----
    _msb_cache: Dict[Tuple[str, Tuple[int, ...]], Tuple[int, ...]] = {}          # cache da ordem MSB
    _fixed_ranges: Dict[Tuple, Tuple[int, int]] = {}                              # (pid, padrao) -> (ini,fim)
    _fixed_lock = threading.Lock()

    def __init__(self, pointer):
        self.pointer = pointer

        # Cache de varredura por chamada de achar_range (com flags)
        self._range_cache: Dict[Tuple, Tuple[Optional[int], Optional[int]]] = {}
        self._range_cache_lock = threading.Lock()

        # IGNORE: conjuntos exatos (str e bytes)
        self._ignore_str: Set[str] = set(self.MOBS_IGNORAR)
        self._ignore_bytes: Set[bytes] = {s.encode('ascii', errors='ignore') for s in self._ignore_str}

        # Adiciona o próprio nome (se existir)
        try:
            myname = self.pointer.get_nome_char()
            if myname:
                if isinstance(myname, bytes):
                    myname_b = myname.split(b'\x00', 1)[0]
                    myname_s = myname_b.decode('ascii', errors='ignore')
                else:
                    myname_s = str(myname)
                    myname_b = myname_s.encode('ascii', errors='ignore')
                self._ignore_str.add(myname_s)
                self._ignore_bytes.add(myname_b)
        except Exception:
            pass

        # Cache de MSBs com hit por PID (ordenação dinâmica)
        self._msb_result_cache: Dict[Tuple[int, int], Tuple[int, int]] = {}  # (pid,msb)->(ini,fim)
        self._msb_hit_order: Dict[int, List[int]] = {}                       # pid-> [msbs com sucesso]

    # ----------------- Iterador de regiões (VirtualQueryEx) -----------------
    def _iter_regions(self, process_handle) -> Iterable[Tuple[int, int, MEMORY_BASIC_INFORMATION]]:
        addr = 0
        mbi = MEMORY_BASIC_INFORMATION()
        sizeof_mbi = ctypes.sizeof(mbi)

        while True:
            got = VirtualQueryEx(process_handle, ctypes.c_void_p(addr), ctypes.byref(mbi), sizeof_mbi)
            if not got:
                break

            base = ctypes.cast(mbi.BaseAddress, ctypes.c_void_p).value
            if base is None:
                base = 0

            size = int(mbi.RegionSize)
            if size == 0:
                break

            yield (base, size, MEMORY_BASIC_INFORMATION.from_buffer_copy(mbi))

            next_addr = base + size
            if next_addr <= addr:
                break
            addr = next_addr

    # ----------------- Helpers de região fixa -----------------
    def _fixed_key(self, padrao: bytes) -> Tuple[int, bytes]:
        pid = getattr(self.pointer.pm, "process_id", None)
        return (pid, padrao)

    def _region_alive_and_readable(self, base: int) -> bool:
        """Valida se o endereço ainda está em região COMMIT legível."""
        mbi = MEMORY_BASIC_INFORMATION()
        got = VirtualQueryEx(self.pointer.pm.process_handle,
                             ctypes.c_void_p(base),
                             ctypes.byref(mbi),
                             ctypes.sizeof(mbi))
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

    def _get_fixed_range(self, padrao: bytes) -> Tuple[Optional[int], Optional[int]]:
        key = self._fixed_key(padrao)
        with self._fixed_lock:
            rng = self._fixed_ranges.get(key)
        if not rng:
            return None, None
        b0, b1 = rng
        if self._region_alive_and_readable(b0):
            return b0, b1
        # inválido → descarta
        with self._fixed_lock:
            self._fixed_ranges.pop(key, None)
        return None, None

    def _set_fixed_range(self, padrao: bytes, base_inicio: int, base_fim: int) -> None:
        key = self._fixed_key(padrao)
        with self._fixed_lock:
            self._fixed_ranges[key] = (base_inicio, base_fim)

    # ----------------- Wrapper cacheado do finder -----------------
    def achar_range_private_prefix_cached(self,
                                          *,
                                          padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                          bloco_leitura=0x40000,
                                          margem=0x800,
                                          exigir_rw=True,
                                          msb: int = 0x0E,
                                          require_region_msb: bool = True,
                                          use_msb_band_hint: bool = True,
                                          force_refresh: bool = False) -> Tuple[Optional[int], Optional[int]]:
        pid = getattr(self.pointer.pm, "process_id", None)
        key = (pid, msb, padrao, exigir_rw, bloco_leitura, margem, require_region_msb, use_msb_band_hint)

        if not force_refresh:
            with self._range_cache_lock:
                hit = self._range_cache.get(key)
                if hit:
                    return hit

        base_inicio, base_fim = self.achar_range_private_prefix_e32(
            padrao=padrao,
            bloco_leitura=bloco_leitura,
            margem=margem,
            exigir_rw=exigir_rw,
            msb=msb,
            require_region_msb=require_region_msb,
            use_msb_band_hint=use_msb_band_hint
        )

        with self._range_cache_lock:
            self._range_cache[key] = (base_inicio, base_fim)

        return base_inicio, base_fim

    # ----------------- Core: encontrar range por MSB -----------------
    def achar_range_private_prefix_e32(self,
                                       padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                       bloco_leitura=0x40000,  # 256 KB
                                       margem=0x800,           # 2 KB nas pontas
                                       exigir_rw=True,
                                       msb: int = 0x0E,
                                       require_region_msb: bool = True,
                                       use_msb_band_hint: bool = True) -> Tuple[Optional[int], Optional[int]]:

        def _is_rw(protect: int) -> bool:
            if protect & PAGE_GUARD:
                return False
            return bool(protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE))

        def _low32(addr: int) -> int:
            return int(addr) & 0xFFFFFFFF

        def _has_msb(addr: int, wanted_msb: int) -> bool:
            try:
                low = _low32(addr)
            except Exception:
                return False
            return ((low >> 24) & 0xFF) == (wanted_msb & 0xFF)

        def _region_intersects_msb_band(region_start: int, size: int, wanted_msb: int) -> bool:
            if size <= 0:
                return False
            region_end = region_start + size - 1
            band_lo = (wanted_msb & 0xFF) << 24
            band_hi = ((wanted_msb + 1) & 0xFF) << 24
            probes = (region_start, region_start + (size // 2), region_end)
            for p in probes:
                l32 = _low32(p)
                if band_lo <= l32 < band_hi:
                    return True
            return False

        carry_len = max(0, len(padrao) - 1)

        for region_start, size, mbi in self._iter_regions(self.pointer.pm.process_handle):
            if mbi.State != MEM_COMMIT:
                continue
            if mbi.Type != MEM_PRIVATE:
                continue
            if exigir_rw and not _is_rw(mbi.Protect):
                continue

            if require_region_msb:
                if not _has_msb(region_start, msb):
                    continue
            else:
                if use_msb_band_hint and not _region_intersects_msb_band(region_start, size, msb):
                    continue

            region_end = region_start + size
            addr = region_start
            prev_tail = b""

            first_hit = None
            last_hit = None
            hits_count = 0

            while addr < region_end:
                tam = min(bloco_leitura, region_end - addr)
                try:
                    buf = self.pointer.pm.read_bytes(addr, tam)
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

                    if not _has_msb(hit, msb):
                        continue

                    if first_hit is None:
                        first_hit = hit
                    last_hit = hit
                    hits_count += 1

                prev_tail = scan_buf[-carry_len:] if carry_len and len(scan_buf) >= carry_len else b""
                addr += tam

            if hits_count > 0:
                base_inicio = max(first_hit - margem, 0)
                base_fim = last_hit + margem
                return base_inicio, base_fim

        return None, None

    # ----------------- Ordem MSB: rápida com print e cache -----------------
    @staticmethod
    @lru_cache(maxsize=128)
    def _build_msb_order(charset: str = "0-9A-Z",
                         start_hints: Tuple[int, ...] = ()) -> Tuple[int, ...]:
        key = (charset, start_hints)
        if key in BuscarPersoangemProximoService._msb_cache:
            return BuscarPersoangemProximoService._msb_cache[key]

        print(f"[MSB] INICIO _build_msb_order charset={charset} hints={start_hints}")
        t0 = time.perf_counter()

        base = BuscarPersoangemProximoService._MSB_BASE_ORDERS.get(charset)
        if base is None:
            seq = []
            if "0-9" in charset:
                seq.extend(range(0x00, 0x0A))
            if "A-Z" in charset:
                seq.extend(range(0x0A, 0x24))
            base = tuple(seq)

        if not start_hints:
            BuscarPersoangemProximoService._msb_cache[key] = base
            dt = (time.perf_counter() - t0) * 1000.0
            print(f"[MSB] FIM _build_msb_order -> len={len(base)} tempo={dt:.3f} ms")
            return base

        base_set = set(base)
        seen = [False] * 256
        prefix = []
        for h in start_hints:
            h &= 0xFF
            if h in base_set and not seen[h]:
                seen[h] = True
                prefix.append(h)

        if not prefix:
            BuscarPersoangemProximoService._msb_cache[key] = base
            dt = (time.perf_counter() - t0) * 1000.0
            print(f"[MSB] FIM _build_msb_order -> len={len(base)} (sem hints válidos) tempo={dt:.3f} ms")
            return base

        tail = [x for x in base if not seen[x]]
        out = tuple(prefix + tail)
        BuscarPersoangemProximoService._msb_cache[key] = out

        dt = (time.perf_counter() - t0) * 1000.0
        print(f"[MSB] FIM _build_msb_order -> len={len(out)} tempo={dt:.3f} ms")
        return out

    # ----------------- Scanner (usa fixed range → otimização MSB) -----------------
    def listar_nomes_e_coords_por_padrao(self,
                                         padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                         bloco_leitura=0x40000,
                                         name_delta=0x74,
                                         name_max=16,
                                         xy_max=4096,
                                         start_hints=(0x0E, 0x0F, 0x0A, 0x08, 0x0B),
                                         force_refresh=False,
                                         mobs_ignorar=None) -> List[dict]:

        # Mesclar lista extra de ignores (EXATOS)
        if mobs_ignorar:
            for s in mobs_ignorar:
                if isinstance(s, bytes):
                    s_b = s.split(b'\x00', 1)[0]
                    s_s = s_b.decode('ascii', errors='ignore')
                else:
                    s_s = str(s)
                    s_b = s_s.encode('ascii', errors='ignore')
                self._ignore_str.add(s_s)
                self._ignore_bytes.add(s_b)

        # 1) TENTAR RANGE FIXO PRIMEIRO (instantâneo)
        if not force_refresh:
            f_ini, f_fim = self._get_fixed_range(padrao)
            if f_ini and f_fim and f_ini < f_fim:
                res = self._scan_range_core(f_ini, f_fim, padrao, bloco_leitura, name_delta, name_max, xy_max)
                if res:
                    return res

        # 2) GERA ORDEM MSB (rápida)
        msb_order = self._build_msb_order(charset="0-9A-Z", start_hints=tuple(start_hints))

        # 2.1) Normaliza hints (ints 0..255), preserva ordem e filtra só os presentes em msb_order
        msb_order_set = set(msb_order)
        hints_clean = []
        seen = set()
        for h in start_hints:
            v = int(h) & 0xFF
            if v in msb_order_set and v not in seen:
                hints_clean.append(v)
                seen.add(v)

        # 3) FASE 1 — TENTAR TODOS OS START_HINTS SEM EARLY-ABORT
        pid = getattr(self.pointer.pm, "process_id", None)
        # print(f"[SCAN] Testando hints (sem abort): {list(map(hex, hints_clean))}")
        for msb in hints_clean:
            # cache MSB->range anterior
            rng = self._msb_result_cache.get((pid, msb))
            if rng:
                b0, b1 = rng
                if b0 and b1 and b0 < b1:
                    res = self._scan_range_core(b0, b1, padrao, bloco_leitura, name_delta, name_max, xy_max)
                    if res:
                        print(f"[SCAN] Cache hit MSB={hex(msb)} (hints) ({len(res)} resultados)")
                        return res
            # três tentativas rápidas
            for margem, req_msb, hint in ((0x800, True, True),
                                          (0x1000, False, True),
                                          (0x2000, False, False)):
                b0, b1 = self.achar_range_private_prefix_cached(
                    padrao=padrao, bloco_leitura=bloco_leitura, margem=margem,
                    exigir_rw=True, msb=msb, require_region_msb=req_msb,
                    use_msb_band_hint=hint, force_refresh=force_refresh
                )
                if b0 and b1 and b0 < b1:
                    res = self._scan_range_core(b0, b1, padrao, bloco_leitura, name_delta, name_max, xy_max)
                    if res:
                        # salvar MSB com sucesso (ordenação futura)
                        self._msb_result_cache[(pid, msb)] = (b0, b1)
                        hits = self._msb_hit_order.get(pid, [])
                        self._msb_hit_order[pid] = [msb] + [m for m in hits if m != msb]
                        # salvar RANGE FIXO para padrao
                        self._set_fixed_range(padrao, b0, b1)
                        print(
                            f"[SCAN] Encontrado (hints) MSB={hex(msb)} base={hex(b0)}..{hex(b1)} ({len(res)} resultados)")
                        return res

        # 4) FASE 2 — RESTANTE (com early-abort)
        pid = getattr(self.pointer.pm, "process_id", None)
        hits = self._msb_hit_order.get(pid, [])
        # ordered = hits + (resto de msb_order que não está nem em hints nem em hits)
        excluded = set(hints_clean)
        ordered = list(hits) + [m for m in msb_order if m not in excluded and m not in hits]

        consecutive_misses = 0
        MAX_MISSES = 3
        # print(f"[SCAN] Restante com early-abort: primeiros={list(map(hex, ordered[:8]))} (total={len(ordered)})")

        for msb in ordered:
            rng = self._msb_result_cache.get((pid, msb))
            if rng:
                b0, b1 = rng
                if b0 and b1 and b0 < b1:
                    res = self._scan_range_core(b0, b1, padrao, bloco_leitura, name_delta, name_max, xy_max)
                    if res:
                        print(f"[SCAN] Cache hit MSB={hex(msb)} (resto) ({len(res)} resultados)")
                        return res
                # mesmo com cache, se não deu resultado, conta como miss
                consecutive_misses += 1
                if consecutive_misses >= MAX_MISSES:
                    # print(f"[SCAN] Abortado após {MAX_MISSES} misses consecutivos (resto)")
                    break
                continue

            # três tentativas rápidas
            found_here = False
            for margem, req_msb, hint in ((0x800, True, True),
                                          (0x1000, False, True),
                                          (0x2000, False, False)):
                b0, b1 = self.achar_range_private_prefix_cached(
                    padrao=padrao, bloco_leitura=bloco_leitura, margem=margem,
                    exigir_rw=True, msb=msb, require_region_msb=req_msb,
                    use_msb_band_hint=hint, force_refresh=force_refresh
                )
                if b0 and b1 and b0 < b1:
                    res = self._scan_range_core(b0, b1, padrao, bloco_leitura, name_delta, name_max, xy_max)
                    if res:
                        self._msb_result_cache[(pid, msb)] = (b0, b1)
                        self._msb_hit_order[pid] = [msb] + [m for m in hits if m != msb]
                        self._set_fixed_range(padrao, b0, b1)
                        print(
                            f"[SCAN] Encontrado (resto) MSB={hex(msb)} base={hex(b0)}..{hex(b1)} ({len(res)} resultados)")
                        return res
                    found_here = True  # achou range, mas scan vazio → ainda assim reset misses

            if found_here:
                consecutive_misses = 0
            else:
                consecutive_misses += 1
                if consecutive_misses >= MAX_MISSES:
                    # print(f"[SCAN] Abortado após {MAX_MISSES} misses consecutivos (resto)")
                    break

        print("[SCAN] Nenhum resultado.")
        return []

    # ----------------- Corpo do scan (reutilizável) -----------------
    def _scan_range_core(self, base_inicio: int, base_fim: int,
                         padrao: bytes, bloco_leitura: int,
                         name_delta: int, name_max: int, xy_max: int) -> List[dict]:
        """Extrai nomes/coords dentro de um range. Usa filtros de ignore otimizados."""
        need_before = 8
        carry_len = need_before + len(padrao) - 1
        resultados, vistos = [], set()
        addr, prev_tail = base_inicio, b""

        ignore_bytes = self._ignore_bytes
        ignore_str = self._ignore_str

        while addr < base_fim:
            tam = min(bloco_leitura, base_fim - addr)
            try:
                buf = self.pointer.pm.read_bytes(addr, tam)
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

                ap = scan_base + pos  # addr_padrao

                # coords
                try:
                    y = self.pointer.pm.read_ushort(ap - 8)
                    x = self.pointer.pm.read_ushort(ap - 4)
                    if not (0 < x < xy_max and 0 < y < xy_max):
                        continue
                except Exception:
                    continue

                # nome (fast ignore por bytes)
                nome_addr = ap - name_delta
                nome = None
                try:
                    raw = self.pointer.pm.read_bytes(nome_addr, name_max)
                    end0 = raw.find(b"\x00")
                    raw0 = raw[:end0] if end0 != -1 else raw
                    if raw0 in ignore_bytes:
                        continue
                    cand_b = bytes(b for b in raw0 if 32 <= b <= 126).strip()
                    if 3 <= len(cand_b) <= name_max:
                        nome = cand_b.decode("ascii", errors="ignore")
                        if nome in ignore_str:
                            continue
                except Exception:
                    pass

                if not nome:
                    try:
                        pre_ini = max(base_inicio, nome_addr)
                        pre_len = min(64, ap - pre_ini)
                        if pre_len > 0:
                            pre = self.pointer.pm.read_bytes(pre_ini, pre_len)
                            j = len(pre) - 1
                            while j >= 0 and pre[j] == 0: j -= 1
                            end = j
                            while j >= 0 and 32 <= pre[j] <= 126: j -= 1
                            cand = pre[j + 1:end + 1].strip()
                            if 3 <= len(cand) <= name_max:
                                if cand in ignore_bytes:
                                    continue
                                nome = cand.decode("ascii", errors="ignore")
                                if nome in ignore_str:
                                    continue
                    except Exception:
                        pass

                key = (ap, x, y)
                if key in vistos:
                    continue
                vistos.add(key)

                resultados.append({
                    "nome": nome,
                    "x": x,
                    "y": y,
                    "addr_padrao": hex(ap),
                    "addr_nome": hex(nome_addr) if nome is not None else None,
                })

            prev_tail = scan_buf[-carry_len:] if len(scan_buf) >= carry_len else scan_buf
            addr += tam

        return resultados

    # ----------------- Pós-processamento: ordenar próximos -----------------
    def ordenar_proximos(self,
                         resultados: List,
                         limite: Optional[int] = None,
                         incluir_dist: bool = True) -> List[dict]:
        """
        Filtra e ordena resultados próximos (|dx|<=10 e |dy|<=10) em relação às coords do self.
        Aceita dicts {"nome", "x", "y", ...} ou tuplas (addr, x, y).
        """
        x0 = self.pointer.get_cood_x()
        y0 = self.pointer.get_cood_y()
        if x0 is None or y0 is None:
            print("[WARN] Coordenadas atuais indisponíveis.")
            return []

        proximos = []

        for item in resultados:
            try:
                if isinstance(item, dict):
                    x = item.get("x"); y = item.get("y")
                    nome = item.get("nome")
                    addr_padrao = item.get("addr_padrao")
                    addr_nome = item.get("addr_nome")
                    addr_candidate = addr_padrao or addr_nome or item.get("addr") or item.get("address")
                    if addr_candidate is None:
                        addr_candidate = item.get("addr_hex")
                    addr_raw = addr_candidate
                else:
                    addr_raw, x, y = item[0], item[1], item[2]
                    nome = None; addr_padrao = None; addr_nome = None

                if x is None or y is None:
                    continue
                x = int(x); y = int(y)
            except Exception as e:
                print(f"[WARN] item ignorado (formato inválido): {item} -> {e}")
                continue

            dx = x - x0; dy = y - y0
            if abs(dx) <= 10 and abs(dy) <= 10:
                dist = abs(dx) + abs(dy)

                addr_str = None
                if addr_raw is not None:
                    try:
                        addr_str = hex(addr_raw) if isinstance(addr_raw, int) else str(addr_raw)
                    except Exception:
                        addr_str = str(addr_raw)

                sort_addr_val = 0
                if isinstance(addr_str, str):
                    try:
                        s = addr_str.strip()
                        sort_addr_val = int(s, 16) if s.lower().startswith("0x") else int(s)
                    except Exception:
                        sort_addr_val = abs(hash(addr_str)) & 0x7FFFFFFF

                proximos.append({
                    "addr": addr_str,
                    "x": x,
                    "y": y,
                    "dist": dist,
                    "nome": nome,
                    "addr_padrao": addr_padrao,
                    "addr_nome": addr_nome,
                    "_sort_addr_val": sort_addr_val
                })

        proximos.sort(key=lambda d: (d["dist"], d["_sort_addr_val"]))

        if limite is not None:
            proximos = proximos[:limite]

        resultado_final = []
        for d in proximos:
            out = {"x": d["x"], "y": d["y"]}
            if incluir_dist:
                out["dist"] = d["dist"]
            if d.get("nome") is not None:
                out["nome"] = d["nome"]
            resultado_final.append(out)

        return resultado_final
