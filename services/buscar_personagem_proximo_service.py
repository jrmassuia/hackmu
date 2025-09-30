import ctypes
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

    def __init__(self, pointer):
        self.pointer = pointer

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

    # -------- coloque estes dois MÉTODOS dentro da sua classe Pointers --------
    def achar_range_private_prefix_e32(self,
                                       padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                       bloco_leitura=0x40000,  # 256 KB
                                       margem=0x800,  # 2 KB nas pontas
                                       exigir_rw=True):  # só PRIVATE com RW/ERW
        """
        Procura a PRIMEIRA região MEM_PRIVATE cujo low32 do endereço-base esteja em 0x0E000000..0x0EFFFFFF
        e que contenha 'padrao'. Dentro dessa região:
          base_inicio = primeiro hit com low32 em 0x0Exxxxxx
          base_fim    = último  hit com low32 em 0x0Exxxxxx
        Retorna (base_inicio, base_fim). Encerra após a 1ª região válida.
        """
        PAGE_READWRITE = 0x04
        PAGE_EXECUTE_READWRITE = 0x40
        PAGE_GUARD = 0x100

        def _is_rw(protect):
            if protect & PAGE_GUARD:
                return False
            return bool(protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE))

        def _low32(addr: int) -> int:
            """Normaliza para valor de 32 bits (unsigned)."""
            return int(addr) & 0xFFFFFFFF

        def _is_e_low32(addr) -> bool:
            """
            Retorna True se o byte mais significativo do low32 for 0x0E ou 0x0F.
            Aceita `addr` como int ou string hex (ex: "0x0E123456").
            """
            try:
                low = _low32(addr)
            except Exception:
                return False

            # extrai o byte mais alto (MSB) do valor low32
            msb = (low >> 24) & 0xFF
            return msb in (0x0E, 0x0F)

        carry_len = max(0, len(padrao) - 1)

        for region_start, size, mbi in self._iter_regions(self.pointer.pm.process_handle):
            if mbi.State != MEM_COMMIT:
                continue
            if mbi.Type != MEM_PRIVATE:
                continue
            if exigir_rw and not _is_rw(mbi.Protect):
                continue
            if not _is_e_low32(region_start):
                continue  # só regiões cujo low32 começa com 0x0E…

            region_end = region_start + size
            addr = region_start
            prev_tail = b""

            first_hit_e = None
            last_hit_e = None
            hits_e_count = 0

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

                    # aceita apenas hits cujo low32 também é 0x0Exxxxxx
                    if not _is_e_low32(hit):
                        continue

                    if first_hit_e is None:
                        first_hit_e = hit
                    last_hit_e = hit
                    hits_e_count += 1

                prev_tail = scan_buf[-carry_len:] if carry_len and len(scan_buf) >= carry_len else b""
                addr += tam

            if hits_e_count > 0:
                base_inicio = max(first_hit_e - margem, 0)
                base_fim = last_hit_e + margem
                # print(f"[PRIVATE_E32] region={hex(region_start)}..{hex(region_end)} "
                #       f"prot={_protect_str(mbi.Protect)} hits_e={hits_e_count}")
                # print(f"[RANGE_E32] base_inicio={hex(base_inicio)} base_fim={hex(base_fim)}")
                return base_inicio, base_fim

        print("[ERRO] Nenhuma região PRIVATE (0x0Exxxxxx) contendo o padrão foi encontrada.")
        return None, None

    def listar_nomes_e_coords_por_padrao(self,
                                         padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                         bloco_leitura=0x40000,
                                         name_delta=0x74,
                                         name_max=16,
                                         xy_max=4096):
        """
        Usa a PRIMEIRA região PRIVATE cujo low32 começa com 0x0E… e que contém o padrão.
        Dentro desse range, lê: Y=@(padrão-8), X=@(padrão-4) e nome=@(padrão-name_delta).
        """
        base_inicio, base_fim = self.achar_range_private_prefix_e32(padrao=padrao, bloco_leitura=bloco_leitura,
                                                                    margem=0x800,
                                                                    exigir_rw=True
                                                                    )
        if not base_inicio or not base_fim or base_inicio >= base_fim:
            print("[ERRO] Range inválido para varredura.")
            return []

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

                # nome
                nome_addr = addr_padrao - name_delta
                nome = None
                try:
                    raw = self.pointer.pm.read_bytes(nome_addr, name_max)
                    end = raw.find(b"\x00");
                    end = len(raw) if end == -1 else end
                    cand = bytes(b for b in raw[:end] if 32 <= b <= 126).strip()
                    if 3 <= len(cand) <= name_max:
                        nome = cand.decode("ascii", errors="ignore")
                except Exception:
                    pass

                if not nome:
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
                                nome = cand.decode("ascii", errors="ignore")
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

                # if nome:
                #     print(f"[OK] {nome}  X={x} Y={y}  (nome @ {hex(nome_addr)}, padrão @ {hex(addr_padrao)})")
                # else:
                #     print(f"[OK] <sem-nome>  X={x} Y={y}  (padrão @ {hex(addr_padrao)})")

            prev_tail = scan_buf[-carry_len:] if len(scan_buf) >= carry_len else scan_buf
            addr += tam

        return resultados

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
