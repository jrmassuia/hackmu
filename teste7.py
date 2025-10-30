import ctypes
import json
from ctypes import wintypes
import pymem
import pymem.process
import win32gui
import win32process

MODULE_NAME = "mucabrasil.exe"
DEFAULT_REGION_SIZE = 0x1000     # aumentei a janela padrão
POINTER_ALIGN = 4
MAX_CHAIN_DEPTH = 3
MAX_POINTERS_TO_REPORT = 300

# --- WinAPI: VirtualQueryEx para testar legibilidade de páginas ---
PAGE_NOACCESS = 0x01
MEM_COMMIT   = 0x1000

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress",       ctypes.c_void_p),
        ("AllocationBase",    ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize",        ctypes.c_size_t),
        ("State",             wintypes.DWORD),
        ("Protect",           wintypes.DWORD),
        ("Type",              wintypes.DWORD),
    ]

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
VirtualQueryEx = kernel32.VirtualQueryEx
VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                           ctypes.POINTER(MEMORY_BASIC_INFORMATION),
                           ctypes.c_size_t]
VirtualQueryEx.restype = ctypes.c_size_t

def is_readable_address(process_handle, addr: int) -> bool:
    mbi = MEMORY_BASIC_INFORMATION()
    res = VirtualQueryEx(process_handle, ctypes.c_void_p(addr),
                         ctypes.byref(mbi), ctypes.sizeof(mbi))
    if res == 0:
        return False
    if mbi.State != MEM_COMMIT:
        return False
    # se a página NÃO é NOACCESS, consideramos legível (há casos com EXECUTE_READ etc.)
    if mbi.Protect == PAGE_NOACCESS:
        return False
    return True


class PointerChainExplorer:
    def __init__(self, pm: pymem.Pymem):
        self.pm = pm
        self.process_handle = pm.process_handle
        self.pid = pm.process_id
        self.module_base, self.module_size = self._get_module_range(MODULE_NAME)
        if not self.module_base or not self.module_size:
            raise RuntimeError(f"Não encontrei {MODULE_NAME}.")
        self.ptr_size = 8 if pm.base_address and pm.base_address > 0xFFFFFFFF else 4

    def _get_module_range(self, module_name: str):
        mod = pymem.process.module_from_name(self.pm.process_handle, module_name)
        return mod.lpBaseOfDll, mod.SizeOfImage

    def _inside_module(self, value: int) -> bool:
        return self.module_base <= value < (self.module_base + self.module_size)

    def _read_ptr_at(self, addr: int):
        try:
            if not is_readable_address(self.process_handle, addr):
                return None
            data = self.pm.read_bytes(addr, self.ptr_size)
            return int.from_bytes(data, "little", signed=False)
        except Exception:
            return None

    def discover_pointers_in_region(self, base_rva: int,
                                    region_size: int = DEFAULT_REGION_SIZE,
                                    align: int = POINTER_ALIGN,
                                    max_report: int = MAX_POINTERS_TO_REPORT):
        start_addr = self.pm.base_address + base_rva
        results = []
        found = 0
        for off in range(0, region_size, align):
            cell = start_addr + off
            val = self._read_ptr_at(cell)
            if val is None:
                continue
            # <<< diferença chave: aceita ponteiro que aponte para QUALQUER página legível >>>
            if is_readable_address(self.process_handle, val):
                results.append({
                    "offset_relative": off,
                    "address_containing_ptr": cell,
                    "pointed_to": val,
                    "inside_module": self._inside_module(val)
                })
                found += 1
                if found >= max_report:
                    break
        return results

    def follow_chains(self, start_addr: int, max_depth: int = MAX_CHAIN_DEPTH):
        chain = []
        current = start_addr
        seen = set()
        for depth in range(max_depth):
            if current in seen:
                chain.append({"addr": current, "note": "loop_detected"})
                break
            seen.add(current)

            ptr = self._read_ptr_at(current)
            chain.append({
                "addr": current,
                "pointed_to": ptr,
                "inside_module": (self._inside_module(ptr) if ptr else False)
            })
            if ptr is None or not is_readable_address(self.process_handle, ptr):
                break
            current = ptr
        return chain

    def auto_discover_chains(self, base_rva: int,
                             region_size: int = DEFAULT_REGION_SIZE,
                             align: int = POINTER_ALIGN,
                             max_results: int = 200):
        start_addr = self.pm.base_address + base_rva
        pointers = self.discover_pointers_in_region(base_rva, region_size, align, max_results)
        chains = []
        for p in pointers:
            chain = self.follow_chains(p["address_containing_ptr"])
            # anota offsets relativos ao início da região
            for n in chain:
                if "addr" in n:
                    n["offset_from_region_start"] = n["addr"] - start_addr
            chains.append({
                "base_region_start": start_addr,
                "initial_pointer_offset": p["offset_relative"],
                "initial_pointer_address": p["address_containing_ptr"],
                "initial_points_to": p["pointed_to"],
                "initial_points_to_inside_module": p["inside_module"],
                "chain": chain
            })
        chains.sort(key=lambda c: c["initial_pointer_offset"])
        return chains


class LeitorAuto:
    def __init__(self, hwnd):
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        self.pm = pymem.Pymem()
        self.pm.open_process_from_id(pid)
        self.explorer = PointerChainExplorer(self.pm)

    def auto_scan(self, base_rva: int, region_size: int = DEFAULT_REGION_SIZE):
        start_addr = self.pm.base_address + base_rva
        print(f"Base RVA: 0x{base_rva:08X}; cliente base: 0x{self.pm.base_address:08X}")
        print(f"Start addr (CLIENT+RVA): 0x{start_addr:08X}")
        chains = self.explorer.auto_discover_chains(base_rva, region_size)
        for c in chains:
            print("----------------------------------------------------------")
            print(f"PTR @+0x{c['initial_pointer_offset']:06X}  (0x{c['initial_pointer_address']:010X})"
                  f" -> 0x{c['initial_points_to']:010X}  "
                  f"(inside_module={c['initial_points_to_inside_module']})")
            for i, n in enumerate(c["chain"]):
                if "addr" in n:
                    print(f"  [{i}] addr=0x{n['addr']:010X}  off_rel=0x{n['offset_from_region_start']:06X}  "
                          f"-> 0x{(n['pointed_to'] if n['pointed_to'] else 0):010X}  "
                          f"in_module={n['inside_module']}")
                else:
                    print(f"  [{i}] {n}")
        print("Total chains found:", len(chains))
        return chains



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
# ------------------------------------------------------------
# Executar como script (exemplo)
# ------------------------------------------------------------
if __name__ == "__main__":
    # Substitua pelo handle real (obtido por exemplo com win32gui.FindWindow)
    # Substitua 'hwnd' pelo handle real da janela do MU que você já tem
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
    hwnd = find_window_handle_by_partial_title(window_title)

    if hwnd is None:
        print("Defina 'hwnd' com o handle da janela do MU antes de executar.")
    else:
        leitor = LeitorAuto(hwnd)
        # Exemplo: varre a partir de CLIENT + 0x03524634 automaticamente
        chains = leitor.auto_scan(base_rva=0x03524634, region_size=0x800)
        # opcional: salvar em arquivo JSON
        with open("memory_chains.json", "w", encoding="utf-8") as f:
            json.dump(chains, f, indent=2, ensure_ascii=False)

