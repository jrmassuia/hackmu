import pymem
import win32gui
import ctypes
from ctypes import wintypes
from utils import mouse_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
import struct

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


def _is_readable(protect: int) -> bool:
    if protect & PAGE_GUARD:
        return False
    return bool(protect & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE))


def _type_str(t):
    if t == MEM_PRIVATE: return "PRIVATE"
    if t == MEM_MAPPED:  return "MAPPED"
    if t == MEM_IMAGE:   return "IMAGE"
    return hex(t)


def _protect_str(p):
    flags = []
    if p & PAGE_READONLY:          flags.append("R")
    if p & PAGE_READWRITE:         flags.append("RW")
    if p & PAGE_EXECUTE_READ:      flags.append("XR")
    if p & PAGE_EXECUTE_READWRITE: flags.append("XRW")
    if p & PAGE_GUARD:             flags.append("GUARD")
    return "|".join(flags) or hex(p)


def _iter_regions(process_handle):
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


# ==== COLE ESTE MÉTODO DENTRO DA SUA CLASSE Pointers ====
def scan_padrao_sem_filtro(
        pm,
        padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
        bloco_leitura=0x40000,  # 256 KB por leitura (aumente se quiser acelerar)
        margem_range=0x800  # 2 KB de margem ao sugerir o range
):
    """
    Varre TODO o espaço de memória do processo (todas as regiões retornadas por VirtualQueryEx),
    tentando ler cada uma. Não filtra por Type (PRIVATE/MAPPED/IMAGE), nem por Protect.
    Só MEM_FREE é pulada por não ser legível. Sem validação de X/Y.

    Imprime TODOS os endereços onde o 'padrao' aparece e retorna a lista de hits (ints).
    Ao final, sugere um range [first- margem, last + margem].
    """
    process = pm.process_handle

    # carregue estes helpers no seu arquivo se ainda não tiver:
    # - _iter_regions(process) -> yield (base, size, mbi)
    # - _protect_str(mbi.Protect) e _type_str(mbi.Type)

    carry_len = max(0, len(padrao) - 1)
    hits = []

    print(f"[SCAN] Padrão: {padrao.hex()}  | bloco_leitura={hex(bloco_leitura)}")
    total_regs = 0
    for base, size, mbi in _iter_regions(process):
        total_regs += 1

        # Única “exclusão”: MEM_FREE não tem nada pra ler
        MEM_FREE = 0x10000
        if getattr(mbi, "State", 0) == MEM_FREE:
            continue

        region_start = base
        region_end = base + size
        addr = region_start
        prev_tail = b""

        while addr < region_end:
            tam = min(bloco_leitura, region_end - addr)
            try:
                buf = pm.read_bytes(addr, tam)
            except Exception:
                # não consigo ler esse pedaço (proteção/guard/etc) -> pula 0x1000
                addr += 0x1000
                prev_tail = b""
                continue

            scan_base = addr - len(prev_tail)
            scan_buf = (prev_tail + buf) if prev_tail else buf

            # procura TODAS as ocorrências no buffer (sem validação extra)
            i = 0
            while True:
                pos = scan_buf.find(padrao, i)
                if pos == -1:
                    break
                i = pos + 1
                hit = scan_base + pos
                hits.append(hit)
                print(
                    f"[HIT] {hex(hit)}  | region {hex(region_start)}..{hex(region_end)}  "
                    f"type={_type_str(mbi.Type)}  prot={_protect_str(mbi.Protect)}"
                )

            # mantém carry pra não perder ocorrências que cruzam fronteiras de bloco
            prev_tail = scan_buf[-carry_len:] if carry_len and len(scan_buf) >= carry_len else b""
            addr += tam

    if not hits:
        print(f"[RESUMO] Nenhum hit para {padrao.hex()} (regiões percorridas: {total_regs}).")
        return []

    hits.sort()
    first, last = hits[0], hits[-1]
    base_inicio = first - margem_range if first >= margem_range else 0
    base_fim = last + margem_range

    print(
        f"\n[RESUMO] total_hits={len(hits)}  first={hex(first)}  last={hex(last)}  "
        f"regiões_percorridas={total_regs}"
    )
    print(f"[SUGESTAO_RANGE] {hex(base_inicio)} -> {hex(base_fim)}")

    return hits


# -------- coloque estes dois MÉTODOS dentro da sua classe Pointers --------
def achar_range_private_prefix_e32(pm,
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
        return addr & 0xFFFFFFFF

    def _is_e_low32(addr: int) -> bool:
        low = _low32(addr)
        return (low & 0xFF000000) == 0x0E000000  # 0x0Exxxxxx

    carry_len = max(0, len(padrao) - 1)

    for region_start, size, mbi in _iter_regions(pm.process_handle):
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
                buf = pm.read_bytes(addr, tam)
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
            print(f"[PRIVATE_E32] region={hex(region_start)}..{hex(region_end)} "
                  f"prot={_protect_str(mbi.Protect)} hits_e={hits_e_count}")
            print(f"[RANGE_E32] base_inicio={hex(base_inicio)} base_fim={hex(base_fim)}")
            return base_inicio, base_fim

    print("[ERRO] Nenhuma região PRIVATE (0x0Exxxxxx) contendo o padrão foi encontrada.")
    return None, None


def listar_nomes_e_coords_por_padrao(pm,
                                     padrao=b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
                                     bloco_leitura=0x40000,
                                     name_delta=0x74,
                                     name_max=16,
                                     xy_max=4096):
    """
    Usa a PRIMEIRA região PRIVATE cujo low32 começa com 0x0E… e que contém o padrão.
    Dentro desse range, lê: Y=@(padrão-8), X=@(padrão-4) e nome=@(padrão-name_delta).
    """
    base_inicio, base_fim = achar_range_private_prefix_e32(pm,
                                                           padrao=padrao, bloco_leitura=bloco_leitura, margem=0x800,
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
            buf = pm.read_bytes(addr, tam)
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
                y = pm.read_ushort(addr_padrao - 8)
                x = pm.read_ushort(addr_padrao - 4)
                if not (0 < x < xy_max and 0 < y < xy_max):
                    continue
            except Exception:
                continue

            # nome
            nome_addr = addr_padrao - name_delta
            nome = None
            try:
                raw = pm.read_bytes(nome_addr, name_max)
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
                        pre = pm.read_bytes(pre_ini, pre_len)
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

            if nome:
                print(f"[OK] {nome}  X={x} Y={y}  (nome @ {hex(nome_addr)}, padrão @ {hex(addr_padrao)})")
            else:
                print(f"[OK] <sem-nome>  X={x} Y={y}  (padrão @ {hex(addr_padrao)})")

        prev_tail = scan_buf[-carry_len:] if len(scan_buf) >= carry_len else scan_buf
        addr += tam

    return resultados


def main():
    print("Selecione a tela do Mu:\n")
    print("1 - [1/3] MUCABRASIL")
    print("2 - [2/3] MUCABRASIL")
    print("3 - [3/3] MUCABRASIL\n")

    while True:
        try:
            escolha = int(input("Digite o número da tela (1 a 3): "))
            if escolha in [1, 2, 3]:
                break
            else:
                print("Valor inválido. Escolha entre 1, 2 ou 3.")
        except ValueError:
            print("Digite um número válido.")

    window_title = f"[{escolha}/3] MUCABRASIL"
    handle = find_window_handle_by_partial_title(window_title)
    pointer = Pointers(handle)
    # hits = scan_padrao_sem_filtro(pointer.pm)
    itens = listar_nomes_e_coords_por_padrao(pointer.pm)


def find_window_handle_by_partial_title(partial_title):
    # Callback para encontrar a janela pelo título parcial
    def enum_windows_callback(hwnd, handles):
        if partial_title in win32gui.GetWindowText(hwnd):
            handles.append(hwnd)

    # Lista para armazenar os handles encontrados
    handles = []
    win32gui.EnumWindows(enum_windows_callback, handles)
    # Retorna o primeiro handle encontrado ou None
    return handles[0] if handles else None


if __name__ == "__main__":
    main()
