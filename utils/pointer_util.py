import ctypes
import struct
import time
from ctypes import wintypes

import pymem

user32 = ctypes.WinDLL("user32", use_last_error=True)


class Pointers:

    def __init__(self, hwnd, max_retries=3, retry_delay=1.0):
        self.pm = None
        self.MODULE_NAME = "mucabrasil.exe"  # Nome do módulo do jogo

        self.CLIENT = None
        pid = self.get_pid_from_handle(hwnd)

        for tentativa in range(max_retries):
            try:
                self.pm = pymem.Pymem()
                self.pm.open_process_from_id(pid)
                self.CLIENT = self.pm.base_address
                break
            except RuntimeError as e:
                print(f"[ERRO] Tentativa {tentativa + 1}: {e}")
                time.sleep(retry_delay)
        else:
            raise RuntimeError("Não foi possível conectar ao processo após várias tentativas.")

        try:
            # -- NECESSARIOS ATUALIZAR
            self.Y_POINTER = self.get_pointer(self.CLIENT + 0x025B0C44, offsets=[0xA4])
            self.X_POINTER = self.get_pointer(self.CLIENT + 0x025B0C44, offsets=[0xA8])
            #
            self.MAGIA_POINTER = self.get_pointer(self.CLIENT + 0x0008E1DC, offsets=[0x0])
            #
            self.HP_POINTER = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0x28])
            self.HP_POINTER_MAX = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0x28]) + 0x8
            self.SD_POINTER = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0x38])
            self.SD_POINTER_MAX = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0x38]) + 0x4
            self.ZEN_POINTER1 = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0xA80])
            self.NOME_CHAR_POINTER = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0x0])
            self.PONTO_LVL_POINTER = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0x88])
            self.RESET_POINTER = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0x10])
            self.LVL_POINTER = self.get_pointer(self.CLIENT + 0x0352D864, offsets=[0x0]) + 0x0E
            #
            self.MOSTRAR_DESC_POINTER = self.get_pointer(self.CLIENT + 0x0429EBCC, offsets=[0x18])
            #
            self.PK_ATIVO_POINTER = self.get_pointer(self.CLIENT + 0x00141288, offsets=[0x0])
            #
            self.PAINEL_LATERAL_ABERTO_POINTER = self.get_pointer(self.CLIENT + 0x00295554, offsets=[0xA0])
            #
            self.SAL_ATUAL_POINTER = self.get_pointer(self.CLIENT + 0x001816AC, offsets=[0x104])

            # pointer_base = self.CLIENT + 0x0352D864
            # if pointer_base:
            #     print(f"Dump da estrutura em 0x{pointer_base:08X}:")
            #
            #     # Exemplo: ler os primeiros 32 bytes como WORDs
            #     for offset in range(0, 32, 2):  # WORD = 2 bytes
            #         addr = pointer_base + offset
            #         data = self.pm.read_bytes(addr, 2)
            #         value = int.from_bytes(data, byteorder='little', signed=False)
            #         print(f"[0x{offset:02X}] = {value}")



        except Exception as e:
            print(f"[ERRO] Falha ao inicializar ponteiros: {e}")

        try:
            ##PARA ESTUDAR E DESCOBRIR
            pass
            # -- TESTES ----
            # self.ITEM_PICK_POINTER = self.CLIENT + 0x41EB737
            #
            # self.FPS_POINTER = self.get_pointer(self.CLIENT + 0x001D8CA0, offsets=[0x0])
            #
            # self.ITEM_SELECIONADO_INVENTARIO_POINTER = self.get_pointer(self.CLIENT + 0x03A99B38, offsets=[0x3E0])
            # self.QTD_ITEM_SELECIONADO_INVENTARIO_POINTER = self.get_pointer(self.CLIENT + 0x0009193C, offsets=[0xC])
            #
            # self.DETECCAO_SM_DL_MG_PROX_POINTER = self.get_pointer(self.CLIENT + 0x0009A5A8, offsets=[0x20])
            #
            # self.DETECCAO_ELF_PROX_POINTER = self.get_pointer(self.CLIENT + 0x0006AE90,
            #                                                   offsets=[0x5C8, 0x4C, 0x4C, 0x488, 0xF0])
            #
            # self.DETECCAO_MG_PROX_POINTER = self.get_pointer(self.CLIENT + 0x0003A6D0,
            #                                                  offsets=[0x288, 0x138, 0xA40, 0x198, 0x58C])
            #
            # self.DETECCAO_SM_PROX_POINTER = self.get_pointer(self.CLIENT + 0x03A8F4AC,
            #                                                  offsets=[0x180, 0x980, 0x2F8, 0x28, 0x4EC])
        except:
            pass

    def get_pid_from_handle(self, hwnd):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    def get_pointer(self, base, offsets):
        try:
            address = base
            for offset in offsets:
                address = self.pm.read_int(address) + offset
            return address
        except Exception as e:
            print(f"[ERRO] get_pointer falhou: {e}")
            return None

    def read_value(self, address, data_type="byte"):
        if address is None:
            return None
        try:
            if data_type == "byte":
                return self.pm.read_bytes(address, 1)[0]
            elif data_type == "int":
                return self.pm.read_int(address)
            elif data_type == "float":
                return self.pm.read_float(address)
            elif data_type == "string":
                return self.pm.read_string(address)
            elif data_type == "short":
                return self.pm.read_short(address)
            elif data_type == "word":  # unsigned short (16 bits)
                data = self.pm.read_bytes(address, 2)
                return int.from_bytes(data, byteorder='little', signed=False)
            else:
                print(f"[ERRO] Tipo de dado desconhecido: {data_type}")
                return None
        except Exception as e:
            print(f"[WARN] Erro ao ler valor do endereço {hex(address)}: {e}")
            return None

    def teste_pointer_necessarios(self):
        print('HP:' + str(self.get_hp()))
        print('HP MAX:' + str(self.get_hp_max()))
        print('SD:' + str(self.get_sd()))
        print('SD MAX:' + str(self.get_sd_max()))
        print('ZEN:' + str(self.get_zen()))
        print('MAGIA:' + str(self.get_magia()))
        print('Y:' + str(self.get_cood_y()))
        print('X:' + str(self.get_cood_x()))
        print('NOME:' + str(self.get_nome_char()))
        print('PONTO LVL:' + str(self.get_ponto_lvl()))
        print('RESET:' + str(self.get_reset()))
        print('LEVEL:' + str(self.get_lvl()))
        print('PK ATIVO:' + str(self.get_pk_ativo()))
        print('MOSTRA DESC ITEM:' + str(self.get_mostrar_desc_item()))
        print('PAINEL LATERAL ABERTO:' + str(self.get_painel_lateral_aberto_item()))
        print('SALA ATUAL:' + str(self.get_sala_atual()))

    def get_cood_x(self):
        return self.read_value(self.X_POINTER, data_type="int")

    def get_cood_y(self):
        return self.read_value(self.Y_POINTER, data_type="int")

    def get_hp(self):
        return self.read_value(self.HP_POINTER, data_type="int")

    def get_hp_max(self):
        return self.read_value(self.HP_POINTER_MAX, data_type="int")

    def get_sd(self):
        return self.read_value(self.SD_POINTER, data_type="int")

    def get_sd_max(self):
        return self.read_value(self.SD_POINTER_MAX, data_type="int")

    def get_zen(self):
        zen = self.read_value(self.ZEN_POINTER1, data_type="int")
        return zen if zen is not None else 0

    def get_magia(self):
        return self.read_value(self.MAGIA_POINTER, data_type="string")

    def get_nome_char(self):
        return self.read_value(self.NOME_CHAR_POINTER, data_type="string")

    def get_ponto_lvl(self):
        return self.read_value(self.PONTO_LVL_POINTER, data_type="int")

    def get_reset(self):
        return self.read_value(self.RESET_POINTER, data_type="int")

    def get_pk_ativo(self):
        return self.read_value(self.PK_ATIVO_POINTER, data_type="int")

    def get_lvl(self):
        info = self.read_value(self.LVL_POINTER, data_type="word")
        if info:
            return info
        return ''

    def get_mostrar_desc_item(self):
        return self.read_value(self.MOSTRAR_DESC_POINTER, data_type="int")

    def get_painel_lateral_aberto_item(self):
        return self.read_value(self.PAINEL_LATERAL_ABERTO_POINTER, data_type="word")

    def get_sala_atual(self):
        return self.read_value(self.SAL_ATUAL_POINTER, data_type="int")

    def get_item_pick(self):
        return self.read_value(self.ITEM_PICK_POINTER, data_type="string")

    def get_item_selecionado_inventario(self):
        return self.read_value(self.ITEM_SELECIONADO_INVENTARIO_POINTER, data_type="int")

    def get_qtd_item_selecionado_inventario(self):
        qtd = self.read_value(self.QTD_ITEM_SELECIONADO_INVENTARIO_POINTER, data_type="string")
        if isinstance(qtd, int):
            return int(qtd)
        return 0

    # def get_deteccao_inventario(self):
    #     return self.read_value(self.DETECCAO_INVENTARIO_POINTER, data_type="int")

    def imprimir_todos_tipos_do_endereco_memoria(self, endereco_raiz=None, tamanho=0x0B00):
        """
        Lê a estrutura apontada por (CLIENT + 0x0352D864) e imprime todos os tipos
        em cada offset (BYTE/WORD/DWORD/FLOAT), caminhando byte a byte.

        - endereco_raiz: se None, usa self.CLIENT + 0x0352D864 e dereferencia.
                         se você já souber o endereço real da estrutura, passe-o aqui.
        - tamanho: bytes a ler a partir da base da estrutura (ex.: 0x0B00 cobre offsets até ~0xA80).
        """
        import struct

        try:
            if endereco_raiz is None:
                # 1) endereço estático que contém o ponteiro da estrutura
                ptr_addr = self.CLIENT + 0x0352D864
                # ptr_addr = self.CLIENT + 0x0429EBCC
                # 2) deref para obter a base real da estrutura
                struct_base = self.pm.read_int(ptr_addr)  # use read_longlong em processo 64-bit
            else:
                struct_base = endereco_raiz

            if not struct_base:
                print("[ERRO] Ponteiro raiz nulo/zero ao dereferenciar 0x0352D864.")
                return

            print(f"\n📦 Dump da estrutura em 0x{struct_base:08X} ({tamanho} bytes):")

            buffer = self.pm.read_bytes(struct_base, tamanho)

        except Exception as e:
            print(f"[ERRO] Falha ao ler memória: {e}")
            return

        for offset in range(len(buffer)):
            linha = f"[0x{offset:04X}] "

            # BYTE
            b = buffer[offset]
            linha += f"BYTE={b:<3} (0x{b:02X})  "

            # WORD (precisa de +1)
            if offset + 1 < len(buffer):
                w = int.from_bytes(buffer[offset:offset + 2], "little", signed=False)
                linha += f"WORD={w:<5} (0x{w:04X})  "

            # DWORD/FLOAT (precisa de +3)
            if offset + 3 < len(buffer):
                d = int.from_bytes(buffer[offset:offset + 4], "little", signed=False)
                linha += f"DWORD={d:<10} (0x{d:08X})  "
                try:
                    f = struct.unpack("<f", buffer[offset:offset + 4])[0]
                    linha += f"FLOAT={f:.6f}  "
                except Exception:
                    linha += "FLOAT=ERR  "

            print(linha)

        # Extra: tentativa de string ASCII limpa
        try:
            ascii_string = buffer.decode('ascii', errors='ignore')
            limpa = ''.join(c for c in ascii_string if c.isprintable()).strip()
            for stop_char in ['\x00', '\x03', '\n', '\r']:
                if stop_char in limpa:
                    limpa = limpa.split(stop_char)[0]
            print(f"\n🔹 ASCII STRING: '{limpa}'")
        except Exception:
            print("Erro ao decodificar como ASCII string.")

    def procurar_players(self) -> list[tuple[str, int, int]]:
        """Varre toda a memória e busca padrões de coordenadas X/Y (X em offset 0x06, Y em offset 0x04)."""
        base_inicio = 0x0E9C0000
        base_fim = 0x0E9D0000
        bloco_tamanho = 0x80
        encontrados = []

        for endereco in range(base_inicio, base_fim, bloco_tamanho):
            try:
                bloco = self.pm.read_bytes(endereco, bloco_tamanho)

                for i in range(0, bloco_tamanho - 6):
                    # Lê possíveis valores nos offsets i+0x04 (Y) e i+0x06 (X)
                    try:
                        y = struct.unpack("<H", bloco[i + 0x04:i + 0x06])[0]
                        x = struct.unpack("<H", bloco[i + 0x06:i + 0x08])[0]
                        if 0 < x < 255 and 0 < y < 255:
                            encontrados.append((hex(endereco + i), x, y))
                    except:
                        continue

            except Exception as e:
                # Pode logar se quiser: print(f"[ERRO] {hex(endereco)}: {e}")
                continue

        for addr, x, y in encontrados:
            print(f"Player encontrado em {addr} - X: {x}, Y: {y}")

    def ler_offsets(self, tamanho: int = 0x80):
        endereco = 0x0E9CD9DC
        print(f"Lendo {tamanho} bytes a partir do endereço {hex(endereco)}...\n")
        try:
            dados = self.pm.read_bytes(endereco, tamanho)

            for offset in range(0, tamanho - 1, 2):
                try:
                    valor = struct.unpack("<H", dados[offset:offset + 2])[0]
                    print(
                        f"Offset {offset:02X} | Addr {hex(endereco + offset)} | Valor (int): {valor:<5} | Hex: {valor:04X}")
                except:
                    print(f"Offset {offset:02X} | Erro na leitura")
        except Exception as e:
            print(f"Erro ao ler memória: {e}")

    def print_padrao_memoria(self, endereco=0x0E9CDE90, tamanho=32):
        try:
            bloco = self.pm.read_bytes(endereco, tamanho)

            print(f"\n[+] Dump de {tamanho} bytes a partir de {hex(endereco)}:")
            print("Offset | Endereço    | Bytes")
            print("-" * 40)

            for i in range(0, tamanho, 16):
                linha = bloco[i:i + 16]
                hex_line = " ".join(f"{b:02X}" for b in linha)
                print(f"{i:02X}     | {hex(endereco + i)} | {hex_line}")

        except Exception as e:
            print(f"[ERRO] Falha ao ler {hex(endereco)}: {e}")

    def get_pointer_dinamico(self, base_offset: int, offsets: list[int]) -> int | None:
        """Resolve dinamicamente um ponteiro a partir do módulo base + offsets."""
        try:
            endereco = self.CLIENT + base_offset
            for offset in offsets:
                endereco = self.pm.read_int(endereco)
                if endereco == 0:
                    return None
                endereco += offset
            return endereco
        except Exception as e:
            print(f"[ERRO] get_pointer_dinamico falhou: {e}")
            return None

    def print_endereco_pointer_scan(self, pointer_base_offset):

        # offsets = [0x508, 0x748, 0x2C, 0x164, 0x0, 0x5C, 0xA4] DEVIAS
        # base_offset = 0x0087F61C  # do print do Cheat Engine
        offsets = [0x2B0]
        base_offset = pointer_base_offset
        """
        Resolve e printa o endereço final de um pointer scan baseado em:
        módulo base + base_offset, seguido de offsets.
        """
        try:
            endereco = self.CLIENT + base_offset
            # print(f"[INFO] Base inicial: {hex(endereco)}")

            for i, offset in enumerate(offsets):
                endereco_antigo = endereco
                endereco = self.pm.read_int(endereco)
                if endereco == 0:
                    # print(f"[ERRO] Endereço nulo ao acessar offset {i}: {hex(endereco_antigo)}")
                    return None
                # print(f"  [OFFSET {i}] {hex(endereco_antigo)} → {hex(endereco)} + {hex(offset)} = {hex(endereco + offset)}")
                endereco += offset

            # print(f"\n[RESULTADO] Endereço final do ponteiro: {hex(endereco)}")

            # Arredonda para base de memória (zera últimos 4 dígitos hex = 0x0000)
            endereco_base = endereco & 0xFFFF0000
            # print(f"[BASE] Endereço base alinhado: {hex(endereco_base)}")

            return endereco_base

        except Exception as e:
            print(f"[ERRO] Falha ao resolver ponteiro: {e}")
            return None

    def buscar_nome_e_xy_na_memoria(self, nome_procurado, base_inicio, base_fim):
        """
        Busca por um nome específico na memória do processo e lê as coordenadas X e Y logo após o nome.

        :param pm: Instância do pymem.Pymem já conectada ao processo.
        :param nome_procurado: Nome (string) que será buscado na memória.
        :param base_inicio: Endereço de memória inicial para varredura.
        :param base_fim: Endereço de memória final para varredura.
        :return: Lista de tuplas (endereco_encontrado, x, y)
        """
        nome_bytes = nome_procurado.encode("utf-8")
        try:
            memoria = self.pm.read_bytes(base_inicio, base_fim - base_inicio)
        except Exception as e:
            print(f"[!] Erro ao ler memória: {e}")
            return []

        resultados = []

        i = 0
        while i < len(memoria) - len(nome_bytes) - 4:
            if memoria[i:i + len(nome_bytes)] == nome_bytes:
                offset = i + len(nome_bytes)
                x = struct.unpack_from('<H', memoria, offset)[0]
                y = struct.unpack_from('<H', memoria, offset + 2)[0]
                endereco = base_inicio + i
                resultados.append((endereco, x, y))
            i += 1

        for endereco, x, y in resultados:
            print(f"[+] Encontrado em {hex(endereco)} - X: {x}, Y: {y}")

    def _addr_from_point(self, point_result_offset: int, inner_offset: int) -> int | None:
        """
        Resolve endereço a partir de um 'point result':
          addr = *(CLIENT + point_result_offset) + inner_offset
        Retorna None se não conseguir ler.
        """
        try:
            base_ptr = self.pm.read_uint(self.CLIENT + point_result_offset)
            if not base_ptr:
                return None
            return base_ptr + inner_offset
        except Exception as e:
            print(f"[ERRO] _addr_from_point falhou em offset {hex(point_result_offset)}: {e}")
            return None

    def procurar_padrao_coordenadas2(
            self,
            range_inicio_point=0x002E2A94,  # *(CLIENT + range_inicio_point) + range_inicio_offset
            range_inicio_offset=0x0D9C,
            range_fim_point=0x00280028,  # *(CLIENT + range_fim_point) + range_fim_offset
            range_fim_offset=0x050C,
            bloco_leitura=0x100000  # 1 MB por leitura (rápido)
    ):
        """
        Procura o padrão b'\\x80\\xFF\\xFF\\xFF\\xFF\\xFF\\xFF\\xFF' APENAS dentro do range:
          INÍCIO = *(CLIENT + range_inicio_point) + range_inicio_offset
          FIM    = *(CLIENT + range_fim_point)    + range_fim_offset
        Para cada match, lê Y (i-8..i-6) e X (i-4..i-2). Retorna [(addr_hex, x, y), ...].
        """
        # 1) Resolve início e fim do range a partir dos dois point results
        try:
            ptr_ini = self.pm.read_uint(self.CLIENT + range_inicio_point) or 0
            ptr_fim = self.pm.read_uint(self.CLIENT + range_fim_point) or 0
        except Exception as e:
            print(f"[ERRO] Falha ao ler point results do range: {e}")
            return []

        if ptr_ini == 0 or ptr_fim == 0:
            print("[ERRO] Point result do range retornou 0 (estrutura não inicializada?).")
            return []

        base_inicio = ptr_ini + range_inicio_offset
        base_fim = ptr_fim + range_fim_offset
        if base_inicio > base_fim:
            base_inicio, base_fim = base_fim, base_inicio  # garante ordem

        # 2) Varredura simples dentro do range
        padrao = b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        pad_len = len(padrao)
        need_before = 8
        carry_len = need_before + pad_len - 1  # 15 bytes p/ não perder match na borda

        resultados = []
        vistos = set()
        addr = base_inicio
        prev_tail = b""

        while addr < base_fim:
            tam = min(bloco_leitura, base_fim - addr)
            try:
                buf = self.pm.read_bytes(addr, tam)
            except Exception:
                # se falhar a leitura desse pedaço, avança 4KB e segue simples
                addr += 0x1000
                prev_tail = b""
                continue

            scan_base = addr - len(prev_tail)
            scan_buf = prev_tail + buf

            pos = scan_buf.find(padrao)
            while pos != -1:
                if pos >= need_before:
                    endereco_padrao = scan_base + pos
                    if endereco_padrao not in vistos:
                        y_bytes = scan_buf[pos - 8:pos - 6]
                        x_bytes = scan_buf[pos - 4:pos - 2]
                        if len(y_bytes) == 2 and len(x_bytes) == 2:
                            y = int.from_bytes(y_bytes, "little", signed=False)
                            x = int.from_bytes(x_bytes, "little", signed=False)
                            if y != 0 and x != 0:
                                print(f"[+] Padrão em {hex(endereco_padrao)} | Y={y} X={x}")
                                resultados.append((hex(endereco_padrao), x, y))
                                vistos.add(endereco_padrao)
                pos = scan_buf.find(padrao, pos + 1)

            # mantém cauda para pegar matches que cruzam a fronteira de blocos
            prev_tail = scan_buf[-carry_len:] if len(scan_buf) >= carry_len else scan_buf
            addr += tam

        mais_proximos = self.ordenar_proximos_ate_10(resultados, incluir_dist=True, limite=10)

        return mais_proximos

    def ordenar_proximos_ate_10(
            self,
            resultados: list[tuple[str, int, int]],
            limite: int | None = None,
            incluir_dist: bool = False
    ) -> list:
        """
        Mantém SOMENTE resultados dentro de |dx|<=10 e |dy|<=10 em relação às suas coords
        e ordena por proximidade (distância Manhattan).
        resultados: [(addr_hex, x, y), ...]
        limite: retorna só os N mais próximos (opcional).
        incluir_dist: se True, retorna (addr, x, y, dist).
        """
        x0 = self.get_cood_x()
        y0 = self.get_cood_y()
        if x0 is None or y0 is None:
            print("[WARN] Coordenadas atuais indisponíveis.")
            return []

        proximos = []
        for addr, x, y in resultados:
            dx = x - x0
            dy = y - y0
            # filtro 'caixa' de 10 por eixo (consistente com seu uso de raio no código)
            if abs(dx) <= 10 and abs(dy) <= 10:
                dist = abs(dx) + abs(dy)  # Manhattan
                proximos.append((addr, x, y, dist))

        # ordena por distância (e, em empate, por endereço para estabilidade)
        proximos.sort(key=lambda t: (t[3], int(t[0], 16)))

        if limite is not None:
            proximos = proximos[:limite]

        return proximos if incluir_dist else [(a, x, y) for (a, x, y, _d) in proximos]

    def testar_nome_e_coordenadas_no_range(
            self,
            nome: str = "DL_DoMall",
            range_inicio_point: int = 0x002E2A94,
            range_inicio_offset: int = 0x0D9C,
            range_fim_point: int = 0x00280028,
            range_fim_offset: int = 0x050C,
            bloco_leitura: int = 0x100000,  # 1MB
            busca_padrao_max: int = 0x800  # até 2 KB após o nome para achar o padrão
    ):
        """
        Procura o nome (ASCII) dentro do range:
          INÍCIO = *(CLIENT + range_inicio_point) + range_inicio_offset
          FIM    = *(CLIENT + range_fim_point)    + range_fim_offset
        Ao encontrar, busca o padrão b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF' depois do nome
        (até 'busca_padrao_max' bytes) e imprime Nome, Endereço, X, Y.
        Retorna lista de dicts: [{'nome', 'addr_nome', 'addr_padrao', 'x', 'y'}]
        """
        padrao = b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        need_before = 8  # para ler Y e X (Y @ -8..-6, X @ -4..-2)

        # 1) Resolve início e fim do range via point results
        try:
            ptr_ini = self.pm.read_uint(self.CLIENT + range_inicio_point) or 0
            ptr_fim = self.pm.read_uint(self.CLIENT + range_fim_point) or 0
        except Exception as e:
            print(f"[ERRO] Falha ao ler point results do range: {e}")
            return []

        if ptr_ini == 0 or ptr_fim == 0:
            print("[ERRO] Point result do range retornou 0 (estrutura não inicializada?).")
            return []

        base_inicio = ptr_ini + range_inicio_offset
        base_fim = ptr_fim + range_fim_offset
        if base_inicio > base_fim:
            base_inicio, base_fim = base_fim, base_inicio

        # 2) Varre pelo NOME no range (usando find com cauda para pegar borda de blocos)
        resultados = []
        nome_bytes = nome.encode("ascii", errors="ignore")
        carry_len = max(0, len(nome_bytes) - 1)
        addr = base_inicio
        prev_tail = b""

        while addr < base_fim:
            tam = min(bloco_leitura, base_fim - addr)
            try:
                buf = self.pm.read_bytes(addr, tam)
            except Exception:
                # se falhar, avança 4KB e zera cauda
                addr += 0x1000
                prev_tail = b""
                continue

            scan_base = addr - len(prev_tail)
            scan_buf = prev_tail + buf

            pos = scan_buf.find(nome_bytes)
            while pos != -1:
                addr_nome = scan_base + pos
                # 3) Depois do nome, procurar o padrão de coordenadas até 'busca_padrao_max' bytes
                search_start = addr_nome + len(nome_bytes)
                # pequena proteção: se search_start < base_inicio, ajusta
                if search_start < base_inicio:
                    search_start = base_inicio

                # leitura de uma janelinha pra buscar o padrão
                try:
                    janela = min(busca_padrao_max, base_fim - search_start)
                    if janela > 0:
                        janela_bytes = self.pm.read_bytes(search_start, janela)
                    else:
                        janela_bytes = b""
                except Exception:
                    janela_bytes = b""

                p = janela_bytes.find(padrao) if janela_bytes else -1
                if p != -1:
                    addr_padrao = search_start + p
                    try:
                        # lê Y e X diretamente da memória (evita borda de buffer)
                        y = self.pm.read_ushort(addr_padrao - 8)
                        x = self.pm.read_ushort(addr_padrao - 4)
                        if y != 0 and x != 0:
                            info = {
                                "nome": nome,
                                "addr_nome": hex(addr_nome),
                                "addr_padrao": hex(addr_padrao),
                                "x": x,
                                "y": y,
                            }
                            resultados.append(info)
                            print(
                                f"[OK] Nome '{nome}' em {info['addr_nome']}  ->  X={x}  Y={y}  (padrão @ {info['addr_padrao']})")
                    except Exception:
                        pass

                # próxima ocorrência do nome neste buffer
                pos = scan_buf.find(nome_bytes, pos + 1)

            # mantém cauda para não perder match que cruza blocos
            prev_tail = scan_buf[-carry_len:] if carry_len and len(scan_buf) >= carry_len else scan_buf
            addr += tam

        return resultados

    def listar_nomes_e_coords_por_padrao(
            self,
            range_inicio_point=0x006412A0, range_inicio_offset=0x370,
            range_fim_point=0x025FE62C, range_fim_offset=0xE50,
            bloco_leitura=0x100000,  # 1 MB
            name_delta=0x74,  # distância nome -> padrão (observada nos seus logs)
            name_max=16  # tamanho máximo do nome
    ):
        padrao = b'\x80\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        need_before = 8
        carry_len = need_before + len(padrao) - 1  # 15

        # --- range pelo point result ---
        try:
            ptr_ini = self.pm.read_uint(self.CLIENT + range_inicio_point) or 0
            ptr_fim = self.pm.read_uint(self.CLIENT + range_fim_point) or 0
        except Exception as e:
            print(f"[ERRO] range: {e}")
            return []
        if ptr_ini == 0 or ptr_fim == 0:
            print("[ERRO] range zerado (estrutura não inicializada?).")
            return []

        base_inicio = ptr_ini + range_inicio_offset
        base_fim = ptr_fim + range_fim_offset
        if base_inicio > base_fim:
            base_inicio, base_fim = base_fim, base_inicio

        resultados, vistos = [], set()
        addr, prev_tail = base_inicio, b""

        while addr < base_fim:
            tam = min(bloco_leitura, base_fim - addr)
            try:
                buf = self.pm.read_bytes(addr, tam)
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
                try:
                    y = self.pm.read_ushort(addr_padrao - 8)
                    x = self.pm.read_ushort(addr_padrao - 4)
                    if x == 0 or y == 0:
                        continue
                except Exception:
                    continue

                # --- nome em (padrão - name_delta) ---
                nome_addr = addr_padrao - name_delta
                nome = None
                try:
                    raw = self.pm.read_bytes(nome_addr, name_max)
                    # tenta C-string
                    end = raw.find(b"\x00")
                    if end == -1:
                        end = len(raw)
                    cand = bytes(b for b in raw[:end] if 32 <= b <= 126).strip()
                    if 3 <= len(cand) <= name_max:
                        nome = cand.decode("ascii", errors="ignore")
                except Exception:
                    pass

                # fallback: se não achou, tenta uma “palavra ASCII” curtinha ali
                if not nome:
                    try:
                        pre = self.pm.read_bytes(max(base_inicio, nome_addr),
                                                 min(64, addr_padrao - max(base_inicio, nome_addr)))
                        # pega a última sequência ASCII do bloco
                        j = len(pre) - 1
                        while j >= 0 and pre[j] == 0:
                            j -= 1
                        end = j
                        while j >= 0 and 32 <= pre[j] <= 126:
                            j -= 1
                        cand = pre[j + 1:end + 1].strip()
                        if 3 <= len(cand) <= name_max:
                            nome = cand.decode("ascii", errors="ignore")
                    except Exception:
                        pass

                key = (addr_padrao, x, y)
                if key in vistos:
                    continue
                vistos.add(key)

                if nome not in ['Red Knight', 'Mutant', 'Potion Girl', 'Baz the Vault Ke', 'Satyros', 'Death Tree',
                                'Alpha Crust', 'Drakan', 'Great Drakan', 'Phantom Knight', 'Metal Balrog',
                                'Omega Wing', 'Phoenix of Darkn', 'Hero Mutant', 'Tantalos', 'Ice Queen', 'Ice Monster',
                                'Hommerd', 'Sea Worm']:

                    resultados.append({
                        "nome": nome,
                        "addr_nome": hex(nome_addr) if nome is not None else None,
                        "addr_padrao": hex(addr_padrao),
                        "x": x,
                        "y": y,
                    })

                    if nome:
                        print(f"[OK] {nome}  X={x} Y={y}  (nome @ {hex(nome_addr)}, padrão @ {hex(addr_padrao)})")
                    else:
                        print(f"[OK] <sem-nome>  X={x} Y={y}  (padrão @ {hex(addr_padrao)})")

            prev_tail = scan_buf[-carry_len:] if len(scan_buf) >= carry_len else scan_buf
            addr += tam

        return resultados
