import ctypes
import re
import psutil
import pygetwindow as gw
import pymem
from pymem import process

# Parâmetros do Pointer
MODULE_NAME = "mucabrasil.exe"  # Nome do executável do jogo
BASE_POINTER = 0x0234B4B4  # Endereço base do Pointer Result
OFFSETS = [0xA8]


def get_pointer(pm, base, offsets):
    try:
        address = base
        for offset in offsets:  # Navega pelos offsets até o endereço final
            address = pm.read_int(address) + offset
        return address
    except Exception as e:
        print(f"Erro ao calcular o ponteiro: {e}")
        return None


def read_value(pm, address, data_type="byte"):
    try:
        if data_type == "byte":
            return pm.read_bytes(address, 1)[0]  # Lê 1 byte
        elif data_type == "int":
            return pm.read_int(address)  # Lê 4 bytes como inteiro
        elif data_type == "float":
            return pm.read_float(address)  # Lê 4 bytes como float
        else:
            print(f"Tipo de dado desconhecido: {data_type}")
            return None
    except Exception as e:
        # print(f"Erro ao ler valor ({data_type}): {e}")
        return None


def read_string_from_pointer(pm, base_pointer, offset=0, max_length=50):
    try:
        pointer_address = pm.read_int(base_pointer)
        final_address = pointer_address + offset
        byte_data = pm.read_bytes(final_address, max_length)
        string_data = byte_data.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
        return string_data
    except Exception as e:
        print(f"String Error: {e}")
        return "Erro!"


def get_value(pm, module_base):
    # Calcula o endereço base dinâmico do pointer
    dynamic_base_pointer = module_base + BASE_POINTER
    endereco_resolvido = get_pointer(pm, dynamic_base_pointer, OFFSETS)
    print(f"Endereço final: {hex(endereco_resolvido)}")

    # Lê o valor atual no endereço resolvido
    valor_atual = pm.read_int(endereco_resolvido)
    print(f"Valor atual no endereço: {valor_atual}")


def main():
    # Solicita o PID do usuário
    window_title = "[1/3] MUCABRASIL"
    pid = find_pid_by_window_title(window_title)

    # Inicializa o Pymem e abre o processo pelo PID
    pm = pymem.Pymem()
    pm.open_process_from_id(pid)
    CLIENT = pm.base_address
    X_POINTER = get_pointer(pm, CLIENT + 0x0234B4B4, offsets=[0xA8])
    print(read_value(pm, X_POINTER, data_type="int"))

    Y_POINTER = get_pointer(pm, CLIENT + 0x0234B4B4, offsets=[0xA4])
    print(read_value(pm, Y_POINTER, data_type="int"))

    HP_POINTER = get_pointer(pm, CLIENT + 0x032C230C, offsets=[0x28])
    print(read_value(pm, HP_POINTER, data_type="int"))

    SD_POINTER = get_pointer(pm, CLIENT + 0x032C230C, offsets=[0x38])
    print(read_value(pm, SD_POINTER, data_type="int"))

    # while True:
    #     LVL_POINTER = get_pointer(pm, CLIENT + 0x0403722C, offsets=[0xBA0, 0x8, 0x8, 0x1C, 0x4, 0x3F4, 0x614])
    #     lvl = read_value(pm, LVL_POINTER)
    #     if lvl <= 400:
    #         print(lvl)
    #         break

    # name = read_string_from_pointer(pm, CHAR_NAME_POINTER, offset=0x40, max_length=50)
    #
    # if re.match(r"^[\w]+$", name):  # Alfanumérico
    #     print(name)
    #     exit()

    # Segunda tentativa
    # pointer = get_pointer(pm, CLIENT + 0x03F985D0, offsets=[0x40, 0x70, 0x8, 0x40, 0x4, 0x4, 0x14])
    # if pointer:
    #     name = read_string_from_pointer(pm, pointer, offset=0x0, max_length=50)
    #     print(name)
    #     exit()

    # Encontra o endereço base do módulo (mucabrasil.exe)
    # module_base = process.module_from_name(pm.process_handle, MODULE_NAME).lpBaseOfDll
    # get_value(pm, CLIENT)

    # # Pergunta se o usuário quer alterar o valor
    # alterar = input("Deseja alterar o valor? (s/n): ").lower()
    # if alterar == 's':
    # pm.write_int(endereco_resolvido, 112)
    # else:
    #     print("Nenhuma alteração feita.")


def get_pid_from_hwnd(hwnd):
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def find_pid_by_window_title(window_title):
    # Obtém todas as janelas abertas
    windows = gw.getAllTitles()

    # Procura a janela pelo título
    for title in windows:
        if window_title.lower() in title.lower():
            # Obtém a janela correspondente
            window = gw.getWindowsWithTitle(title)[0]
            # Obtém o handle da janela
            hwnd = window._hWnd

            # Obtém o PID usando o handle
            pid = get_pid_from_hwnd(hwnd)
            return pid

    return None


def find_process_pid():
    process_name = "mucabrasil.exe"
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            return proc.info['pid']
    return None


if __name__ == "__main__":
    main()
