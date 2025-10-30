import ctypes
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
            self.Y_POINTER = self.get_pointer(self.CLIENT + 0x025A2A80, offsets=[0xA4])
            self.X_POINTER = self.get_pointer(self.CLIENT + 0x025A2A80, offsets=[0xA8])
            #
            self.MAGIA_POINTER = self.get_pointer(self.CLIENT + 0x0005E84C, offsets=[0x0])
            #
            self.HP_POINTER = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0x28])
            self.HP_POINTER_MAX = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0x28]) + 0x8
            self.SD_POINTER = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0x38])
            self.SD_POINTER_MAX = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0x38]) + 0x4
            self.ZEN_POINTER1 = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0xA80])
            self.NOME_CHAR_POINTER = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0x0])
            self.PONTO_LVL_POINTER = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0x88])
            self.RESET_POINTER = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0x10])
            self.LVL_POINTER = self.get_pointer(self.CLIENT + 0x03524634, offsets=[0x0]) + 0x0E
            #
            self.MOSTRAR_DESC_POINTER = self.get_pointer(self.CLIENT + 0x0422D2A4, offsets=[0x18])
            #
            self.PK_ATIVO_POINTER = self.get_pointer(self.CLIENT + 0x00111188, offsets=[0x0])
            #
            self.CHAR_PK_SELECIONADO_POINTER = self.get_pointer(self.CLIENT + 0x000D6E34, offsets=[0x0])
            #
            self.SALA_ATUAL_POINTER = self.get_pointer(self.CLIENT + 0x0014F3EC, offsets=[0x104])
            #
            self.DESC_INFO_POINTER = self.get_pointer(self.CLIENT + 0x002D0D24, offsets=[0x1DC])
            #
            # pointer_base = self.CLIENT + 0x03524634
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

    def read_value(self, address, data_type="byte", byte=50):
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
                data_bytes = self.pm.read_bytes(address, byte)
                try:
                    null_index = data_bytes.find(b'\x00')
                    if null_index != -1:
                        data_bytes = data_bytes[:null_index]
                    return data_bytes.decode('latin-1')
                except Exception as decode_error:
                    print(f"[WARN] Erro de decodificação de string em {hex(address)}: {decode_error}")
                    return data_bytes.decode('latin-1', errors='replace')

            elif data_type == "short":
                return self.pm.read_short(address)
            elif data_type == "word":
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
        print('PK SELECIONADO:' + str(self.get_char_pk_selecionado()))
        print('MOSTRA DESC ITEM:' + str(self.get_mostrar_desc_item()))
        print('SALA ATUAL:' + str(self.get_sala_atual()))
        print('DESCRIÇÃO INFO:' + self.get_descricao_info())

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

    def get_char_pk_selecionado(self):
        valor = int(self.read_value(self.CHAR_PK_SELECIONADO_POINTER, data_type="word"))
        if valor == 65535:
            return False
        return True

    def get_lvl(self):
        info = self.read_value(self.LVL_POINTER, data_type="word")
        if info:
            return info
        return ''

    def get_mostrar_desc_item(self):
        return self.read_value(self.MOSTRAR_DESC_POINTER, data_type="int")

    def get_sala_atual(self):
        return self.read_value(self.SALA_ATUAL_POINTER, data_type="int")

    def get_descricao_info(self):
        return self.read_value(self.DESC_INFO_POINTER, data_type="string")

    def get_mapa_atual(self):
        # mapa = self.read_value(self.MAPA_ATUAL_POINTER, data_type="string")
        # if mapa:
        #     mapa = mapa.replace('p ', '')
        return None

    def get_item_pick(self):
        # return self.read_value(self.ITEM_PICK_POINTER, data_type="string")
        pass

    def imprimir_todos_tipos_do_endereco_memoria(self, endereco_raiz=None, tamanho=0x0B00):
        """
        Lê a estrutura apontada por (CLIENT + 0x03524634) e imprime todos os tipos
        em cada offset (BYTE/WORD/DWORD/FLOAT), caminhando byte a byte.

        - endereco_raiz: se None, usa self.CLIENT + 0x03524634 e dereferencia.
                         se você já souber o endereço real da estrutura, passe-o aqui.
        - tamanho: bytes a ler a partir da base da estrutura (ex.: 0x0B00 cobre offsets até ~0xA80).
        """
        import struct

        try:
            if endereco_raiz is None:
                # 1) endereço estático que contém o ponteiro da estrutura
                ptr_addr = self.CLIENT + 0x03524634
                # ptr_addr = self.CLIENT + 0x0429EBCC
                # 2) deref para obter a base real da estrutura
                struct_base = self.pm.read_int(ptr_addr)  # use read_longlong em processo 64-bit
            else:
                struct_base = endereco_raiz

            if not struct_base:
                print("[ERRO] Ponteiro raiz nulo/zero ao dereferenciar 0x03524634.")
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

    def print_padrao_memoria(self, endereco=0x0422CAC0, tamanho=32):
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
