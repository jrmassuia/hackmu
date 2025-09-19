from utils.pointer_util import Pointers
import ctypes as C

# ---- Constantes Windows ----
PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
MEM_MAPPED = 0x40000
MEM_IMAGE = 0x1000000

READABLE_PROTS = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}  # READ/WRITE/EXEC_READ combos


class MEMORY_BASIC_INFORMATION(C.Structure):
    _fields_ = [
        ("BaseAddress", C.c_void_p), ("AllocationBase", C.c_void_p),
        ("AllocationProtect", C.c_ulong), ("RegionSize", C.c_size_t),
        ("State", C.c_ulong), ("Protect", C.c_ulong), ("Type", C.c_ulong)
    ]


class ProcurarPlayer:
    def __init__(self, hwnd):
        self.pointer = Pointers(hwnd)
        self.pm = self.pointer.pm
        self.k32 = C.WinDLL("kernel32", use_last_error=True)
        self.proc = self.pm.process_handle
        self._vqex = self.k32.VirtualQueryEx
        self._vqex.argtypes = [C.c_void_p, C.c_void_p, C.POINTER(MEMORY_BASIC_INFORMATION), C.c_size_t]
        self._vqex.restype = C.c_size_t

    # ---------- util: regiões legíveis recortadas ao range ----------
    def _regions_in_range(self, start_addr, end_addr,
                          incluir_private=True, incluir_image=True, incluir_mapped=False):
        tipos_ok = set()
        if incluir_image:   tipos_ok.add(MEM_IMAGE)
        if incluir_private: tipos_ok.add(MEM_PRIVATE)
        if incluir_mapped:  tipos_ok.add(MEM_MAPPED)

        mbi = MEMORY_BASIC_INFORMATION()
        addr = start_addr
        while addr < end_addr:
            if not self._vqex(self.proc, C.c_void_p(addr), C.byref(mbi), C.sizeof(mbi)):
                addr += 0x1000
                continue

            rbase = int(mbi.BaseAddress)
            rsize = int(mbi.RegionSize) or 0x1000
            rnext = rbase + rsize
            # recorta com [start,end)
            clip_start = max(rbase, start_addr)
            clip_end = min(rnext, end_addr)

            if (clip_start < clip_end and
                    int(mbi.State) == MEM_COMMIT and
                    (int(mbi.Protect) & PAGE_GUARD) == 0 and
                    (int(mbi.Protect) & PAGE_NOACCESS) == 0 and
                    int(mbi.Protect) in READABLE_PROTS and
                    int(mbi.Type) in tipos_ok):
                yield clip_start, (clip_end - clip_start)

            addr = rnext

    # ---------- scan de buffer pelo padrão (rápido) ----------
    @staticmethod
    def _scan_xy(base, buf, step=2):
        achados = []
        n = len(buf)
        if n < 8: return achados
        mv = memoryview(buf)
        lim = n - 8
        i = 0
        while i <= lim:
            y0 = mv[i + 0x04];
            y1 = mv[i + 0x05]
            x0 = mv[i + 0x06];
            x1 = mv[i + 0x07]
            if (y0 | y1 | x0 | x1) != 0:
                y = (y1 << 8) | y0
                x = (x1 << 8) | x0
                if 0 < x < 255 and 0 < y < 255:
                    achados.append((hex(base + i), x, y))
            i += step
        return achados

    # ---------- API: varrer um range ----------
    def procurar_players_no_range(self, base_inicio, base_fim,
                                  bloco_leitura=0x100000, step=2,
                                  incluir_private=True, incluir_image=True, incluir_mapped=False):
        resultados = []
        for rbase, rsize in self._regions_in_range(base_inicio, base_fim,
                                                   incluir_private, incluir_image, incluir_mapped):
            off = 0
            while off < rsize:
                tam = min(bloco_leitura, rsize - off)
                addr = rbase + off
                try:
                    buf = self.pm.read_bytes(addr, tam)
                    resultados.extend(self._scan_xy(addr, buf, step=step))
                except Exception:
                    pass
                off += tam
        return resultados

    # ---------- API: passar SÓ o offset; ele resolve o range ----------
    def procurar_players_por_offset(self, offset, janela=0x20000,
                                    bloco_leitura=0x100000, step=2):
        """
        Lê 'ptr = *(CLIENT + offset)' e varre [ptr-janela, ptr+janela).
        - offset: ex. 0x025B0C48
        - janela: metade do range (padrão ±128 KB)
        """
        real = self.pointer.CLIENT + offset
        try:
            ptr = self.pm.read_uint(real)
        except Exception as e:
            raise RuntimeError(f"Falha ao ler *(CLIENT+{hex(offset)}): {e}")

        if not ptr:
            # fallback: varre ao redor do próprio endereço do point (caso esteja zerado temporariamente)
            ini = max(0, real - janela)
            fim = real + janela
        else:
            ini = max(0, ptr - janela)
            fim = ptr + janela

        return self.procurar_players_no_range(ini, fim,
                                              bloco_leitura=bloco_leitura,
                                              step=step,
                                              incluir_private=True,
                                              incluir_image=True,
                                              incluir_mapped=False)
