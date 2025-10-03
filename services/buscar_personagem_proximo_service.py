import ctypes
import threading
from ctypes import wintypes

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
    MOBS_IGNORAR = {
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

    def __init__(self, pointer):
        self.pointer = pointer
        self._range_cache: dict[tuple, tuple[int | None, int | None]] = {}
        self._range_cache_lock = threading.Lock()

        # --- IGNORE: conjuntos exatos (str e bytes) ---
        # Obs.: os nomes do jogo são ASCII/ANSI; usamos encode('ascii', 'ignore') para ter a versão bytes.
        self._ignore_str: set[str] = set(self.MOBS_IGNORAR)
        self._ignore_bytes: set[bytes] = {s.encode('ascii', errors='ignore') for s in self._ignore_str}

        # Adiciona seu próprio nome (se existir) às duas estruturas
        try:
            myname = self.pointer.get_nome_char()
            if myname:
                if isinstance(myname, bytes):
                    myname_b = myname.split(b'\x00', 1)[0]  # corta em null se vier
                    myname_s = myname_b.decode('ascii', errors='ignore')
                else:
                    myname_s = str(myname)
                    myname_b = myname_s.encode('ascii', errors='ignore')

                # match EXATO
                self._ignore_str.add(myname_s)
                self._ignore_bytes.add(myname_b)
        except Exception:
            pass

    def add_mob_ignorar(self, nome) -> bool:
        """
        Adiciona um nome ao conjunto de ignorados (case-insensitive).
        Retorna True se adicionou, False se já existia ou nome inválido.
        Aceita str ou bytes.
        """
        if not nome:
            return False
        if isinstance(nome, bytes):
            # tenta decodificar; ajuste o encoding se necessário no seu client
            nome = nome.decode('utf-8', errors='ignore')

        nome_clean = nome.strip()
        if not nome_clean:
            return False

        key = nome_clean.casefold()
        with self._mobs_lock:
            if key in self._mobs_ignorar_norm:
                return False
            self._mobs_ignorar_raw.add(nome_clean)
            self._mobs_ignorar_norm.add(key)
            return True

    def _is_readable(self, protect: int) -> bool:
        if protect & PAGE_GUARD:
            return False
        return bool(protect & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE))

    def _type_str(self, t):
        if t == MEM_PRIVATE: return "PRIVATE"
        if t == MEM_MAPPED:  return "MAPPED"
        if t == MEM_IMAGE:   return "IMAGE"
        return hex(t)

    def _protect_str(self, p):
        flags = []
        if p & PAGE_READONLY:          flags.append("R")
        if p & PAGE_READWRITE:         flags.append("RW")
        if p & PAGE_EXECUTE_READ:      flags.append("XR")
        if p & PAGE_EXECUTE_READWRITE: flags.append("XRW")
        if p & PAGE_GUARD:             flags.append("GUARD")
        return "|".join(flags) or hex(p)

    def _iter_regions(self, process_handle):
        addr = 0
        mbi = MEMORY_BASIC_INFORMATION()
        sizeof_mbi = ctypes.sizeof(mbi)

        while True:
            got = VirtualQueryEx(process_handle, ctypes.c_void_p(addr), ctypes.byref(mbi), sizeof_mbi)
            if not got:
                # opcional: debug do erro
                # print("VirtualQueryEx falhou em", hex(addr), "GetLastError=", ctypes.get_last_error())
                break

            # BaseAddress pode virar None quando é 0x0. Trate como 0.
            base = ctypes.cast(mbi.BaseAddress, ctypes.c_void_p).value
            if base is None:
                base = 0

            size = int(mbi.RegionSize)
            if size == 0:
                break

            yield (base, size, MEMORY_BASIC_INFORMATION.from_buffer_copy(mbi))

            next_addr = base + size
            if next_addr <= addr:
                # proteção contra loop infinito
                break
            addr = next_addr

    def achar_range_private_prefix_cached(self,
                                          *,
                                          padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                          bloco_leitura=0x40000,
                                          margem=0x800,
                                          exigir_rw=True,
                                          msb: int = 0x0E,
                                          require_region_msb: bool = True,
                                          use_msb_band_hint: bool = True,
                                          force_refresh: bool = False) -> tuple[int | None, int | None]:
        """
        Versão cacheada de achar_range_private_prefix_e32.
        A chave do cache inclui PID, MSB, padrão e demais flags que afetam o resultado.
        """
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

    def limpar_cache_ranges(self):
        """Se quiser invalidar manualmente (troca de mapa, loading, etc.)."""
        with self._range_cache_lock:
            self._range_cache.clear()

    # ---------------------- SUA FUNÇÃO (com melhorias) ----------------------
    def achar_range_private_prefix_e32(self,
                                       padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                       bloco_leitura=0x40000,  # 256 KB
                                       margem=0x800,  # 2 KB nas pontas
                                       exigir_rw=True,
                                       msb: int = 0x0E,
                                       require_region_msb: bool = True,
                                       use_msb_band_hint: bool = True):
        """
        (mesmo corpo que te passei antes, com filtros flexíveis)
        """
        PAGE_READWRITE = 0x04
        PAGE_EXECUTE_READWRITE = 0x40
        PAGE_GUARD = 0x100
        MEM_COMMIT = 0x1000
        MEM_PRIVATE = 0x20000

        def _is_rw(protect):
            if protect & PAGE_GUARD:
                return False
            return bool(protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE))

        def _low32(addr: int) -> int:
            return int(addr) & 0xFFFFFFFF

        def _has_msb(addr, wanted_msb: int) -> bool:
            try:
                low = _low32(addr)
            except Exception:
                return False
            return ((low >> 24) & 0xFF) == wanted_msb

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

            if require_region_msb and not _has_msb(region_start, msb):
                continue
            if not require_region_msb and use_msb_band_hint:
                if not _region_intersects_msb_band(region_start, size, msb):
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

    def _build_msb_order(self, charset: str = "0-9A-Z",
                         start_hints: tuple[int, ...] = ()) -> tuple[int, ...]:
        """
        Gera uma ordem de MSBs.
        - "0-9A-Z": 0..9 e A..Z  => 0..9 e 10..35 (0x00..0x23)
          (A=10, B=11, ..., Z=35)
        Você pode adaptar/estender se quiser outros intervalos.
        start_hints: MSBs para priorizar no início (mantém ordem e remove duplicatas).
        """
        order = []

        # 0-9
        if "0-9" in charset:
            order.extend(range(0x00, 0x0A))  # 0..9

        # A-Z  (A=10 .. Z=35)
        if "A-Z" in charset:
            order.extend(range(0x0A, 0x24))  # 10..35 -> 0x0A..0x23

        # aplica hints no começo e remove duplicatas mantendo ordem estável
        if start_hints:
            hinted = list(start_hints) + [x for x in order if x not in start_hints]
            # normaliza para 0..255 (só por segurança)
            hinted = [x & 0xFF for x in hinted]
            seen = set()
            dedup = []
            for x in hinted:
                if x not in seen:
                    seen.add(x)
                    dedup.append(x)
            return tuple(dedup)

        # sem hints
        seen = set()
        dedup = []
        for x in order:
            x &= 0xFF
            if x not in seen:
                seen.add(x)
                dedup.append(x)
        return tuple(dedup)

    def listar_nomes_e_coords_por_padrao(self,
                                         padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                         bloco_leitura=0x40000,
                                         name_delta=0x74,
                                         name_max=16,
                                         xy_max=4096,
                                         start_hints=(0x0E, 0x0F, 0x0A, 0x08, 0x0B),
                                         force_refresh=False,
                                         mobs_ignorar=None):

        # Se quiser mesclar com uma lista extra vinda por parâmetro (EXATA):
        if mobs_ignorar:
            # adiciona SEM normalização => comparação exata
            for s in mobs_ignorar:
                if isinstance(s, bytes):
                    s_b = s.split(b'\x00', 1)[0]
                    s_s = s_b.decode('ascii', errors='ignore')
                else:
                    s_s = str(s)
                    s_b = s_s.encode('ascii', errors='ignore')
                self._ignore_str.add(s_s)
                self._ignore_bytes.add(s_b)

        def _scan_range(base_inicio: int, base_fim: int):
            need_before = 8
            carry_len = need_before + len(padrao) - 1
            resultados, vistos = [], set()
            addr, prev_tail = base_inicio, b""

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

                    addr_padrao = scan_base + pos

                    # coords
                    try:
                        y = self.pointer.pm.read_ushort(addr_padrao - 8)
                        x = self.pointer.pm.read_ushort(addr_padrao - 4)
                        if not (0 < x < xy_max and 0 < y < xy_max):
                            continue
                    except Exception:
                        continue

                    # nome (fast-path: verificar IGNORE em BYTES antes de decodificar)
                    nome_addr = addr_padrao - name_delta
                    nome = None
                    try:
                        raw = self.pointer.pm.read_bytes(nome_addr, name_max)
                        end0 = raw.find(b"\x00")
                        if end0 != -1:
                            raw0 = raw[:end0]
                        else:
                            raw0 = raw

                        # FAST IGNORE (bytes exatos)
                        if raw0 in self._ignore_bytes:
                            continue  # ignora sem decodificar

                        # Se não ignorou pelos bytes, faz limpeza ASCII básica e decodifica
                        # (mantém a lógica original para montar 'nome' do resultado)
                        cand_bytes = bytes(b for b in raw0 if 32 <= b <= 126).strip()
                        if 3 <= len(cand_bytes) <= name_max:
                            nome = cand_bytes.decode("ascii", errors="ignore")

                            # IGNORE exato em string (redundante na maioria, mas mantém consistência)
                            if nome in self._ignore_str:
                                continue

                    except Exception:
                        pass

                    if not nome:
                        # fallback (pode ser caro; só roda se não ignoramos via bytes/str)
                        try:
                            pre_ini = max(base_inicio, nome_addr)
                            pre_len = min(64, addr_padrao - pre_ini)
                            if pre_len > 0:
                                pre = self.pointer.pm.read_bytes(pre_ini, pre_len)
                                j = len(pre) - 1
                                while j >= 0 and pre[j] == 0: j -= 1
                                end = j
                                while j >= 0 and 32 <= pre[j] <= 126: j -= 1
                                cand = pre[j + 1:end + 1].strip()
                                if 3 <= len(cand) <= name_max:
                                    # checa ignore exato ANTES de decodificar
                                    if cand in self._ignore_bytes:
                                        continue
                                    nome = cand.decode("ascii", errors="ignore")
                                    if nome in self._ignore_str:
                                        continue
                        except Exception:
                            pass

                    key = (addr_padrao, x, y)
                    if key in vistos:
                        continue
                    vistos.add(key)

                    resultados.append({
                        "nome": nome,
                        "x": x,
                        "y": y,
                        "addr_padrao": hex(addr_padrao),
                        "addr_nome": hex(nome_addr) if nome is not None else None,
                    })

                prev_tail = scan_buf[-carry_len:] if len(scan_buf) >= carry_len else scan_buf
                addr += tam

            return resultados

        # resto do método (ordem MSB + cache) permanece igual ao que você já tem
        msb_order = self._build_msb_order(charset="0-9A-Z", start_hints=start_hints)

        for msb in msb_order:
            base_inicio, base_fim = self.achar_range_private_prefix_cached(
                padrao=padrao, bloco_leitura=bloco_leitura, margem=0x800,
                exigir_rw=True, msb=msb, require_region_msb=True, use_msb_band_hint=True,
                force_refresh=force_refresh
            )
            if base_inicio and base_fim and base_inicio < base_fim:
                res = _scan_range(base_inicio, base_fim)
                if res:
                    return res

            base_inicio, base_fim = self.achar_range_private_prefix_cached(
                padrao=padrao, bloco_leitura=bloco_leitura, margem=0x1000,
                exigir_rw=True, msb=msb, require_region_msb=False, use_msb_band_hint=True,
                force_refresh=force_refresh
            )
            if base_inicio and base_fim and base_inicio < base_fim:
                res = _scan_range(base_inicio, base_fim)
                if res:
                    return res

            base_inicio, base_fim = self.achar_range_private_prefix_cached(
                padrao=padrao, bloco_leitura=max(bloco_leitura, 0x80000),
                margem=0x2000, exigir_rw=True, msb=msb,
                require_region_msb=False, use_msb_band_hint=False,
                force_refresh=force_refresh
            )
            if base_inicio and base_fim and base_inicio < base_fim:
                res = _scan_range(base_inicio, base_fim)
                if res:
                    return res

        return []

    from typing import List

    def ordenar_proximos(
            self,
            resultados: list,
            limite: int | None = None,
            incluir_dist: bool = True
    ) -> List[dict]:
        """
        Filtra e ordena resultados próximos (|dx|<=10 e |dy|<=10) em relação às coords do self.
        Aceita `resultados` em dois formatos:
          - dicts: {"nome":..., "x": int, "y": int, "addr_padrao": "0x...", "addr_nome": "0x..."}
          - tuplas/listas: (addr_hex_or_int, x, y)

        Retorna lista de dicionários com pelo menos as chaves:
          - "addr": str   (endereço escolhido, preferindo addr_padrao -> addr_nome -> tuple addr)
          - "x": int
          - "y": int
          - "dist": int   (apenas se incluir_dist == True)
        Quando disponíveis, também inclui "nome", "addr_padrao", "addr_nome".
        """
        x0 = self.pointer.get_cood_x()
        y0 = self.pointer.get_cood_y()
        if x0 is None or y0 is None:
            print("[WARN] Coordenadas atuais indisponíveis.")
            return []

        proximos = []

        for item in resultados:
            # extrai campos de forma robusta
            try:
                if isinstance(item, dict):
                    x = item.get("x")
                    y = item.get("y")
                    nome = item.get("nome")
                    addr_padrao = item.get("addr_padrao")
                    addr_nome = item.get("addr_nome")
                    # prefer addr_padrao, depois addr_nome, depois qualquer chave 'addr'
                    addr_candidate = addr_padrao or addr_nome or item.get("addr") or item.get("address")
                    # se nada, tenta ver se existe 'addr_hex' ou 'address_hex'
                    if addr_candidate is None:
                        addr_candidate = item.get("addr_hex")
                    addr_raw = addr_candidate
                else:
                    # tuple/list: (addr, x, y)
                    addr_raw = item[0]
                    x = item[1]
                    y = item[2]
                    nome = None
                    addr_padrao = None
                    addr_nome = None

                # normalize coords
                if x is None or y is None:
                    # pula entradas sem coords válidas
                    continue
                x = int(x)
                y = int(y)
            except Exception as e:
                print(f"[WARN] item ignorado (formato inválido): {item} -> {e}")
                continue

            dx = x - x0
            dy = y - y0
            if abs(dx) <= 10 and abs(dy) <= 10:
                dist = abs(dx) + abs(dy)  # Manhattan

                # normaliza addr para string de saída
                addr_str = None
                if addr_raw is None:
                    addr_str = None
                else:
                    # se for inteiro -> hex string; se for str, mantém
                    try:
                        if isinstance(addr_raw, int):
                            addr_str = hex(addr_raw)
                        else:
                            addr_str = str(addr_raw)
                    except Exception:
                        addr_str = str(addr_raw)

                # calcula valor numérico para ordenação por endereço (estabilidade)
                sort_addr_val = 0
                if isinstance(addr_str, str):
                    try:
                        s = addr_str.strip()
                        if s.lower().startswith("0x"):
                            sort_addr_val = int(s, 16)
                        else:
                            sort_addr_val = int(s)
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

        # ordena por (dist, endereco_normalizado)
        proximos.sort(key=lambda d: (d["dist"], d["_sort_addr_val"]))

        # aplica limite
        if limite is not None:
            proximos = proximos[:limite]

        # prepara saída final removendo campo auxiliar _sort_addr_val
        resultado_final = []
        for d in proximos:
            out = {
                # "addr": d["addr"],
                "x": d["x"],
                "y": d["y"],
            }
            # if incluir_dist:
            #     out["dist"] = d["dist"]
            if d.get("nome") is not None:
                out["nome"] = d["nome"]
            # if d.get("addr_padrao") is not None:
            #     out["addr_padrao"] = d["addr_padrao"]
            # if d.get("addr_nome") is not None:
            #     out["addr_nome"] = d["addr_nome"]
            resultado_final.append(out)

        return resultado_final
