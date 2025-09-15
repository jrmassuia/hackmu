import ctypes
import os
import time
from ctypes import wintypes

import win32gui

user32 = ctypes.windll.user32


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

    handles_filhos = listar_e_inspecionar_filhos(handle)
    #
    for handle_filho in handles_filhos:
        for i, filho in enumerate([handle_filho]):
            texto = obter_titulo_do_filho(filho)
            if texto == '1':
                print('Buscando nomes...')
                printnomechar(filho)


def printnomechar(handle_filho):
    nomecharanterior = ''
    arquivo = "nomes_chars.txt"

    # Verifica se o arquivo existe e se já tem conteúdo
    if os.path.exists(arquivo):
        with open(arquivo, "r+", encoding="utf-8") as f:
            conteudo = f.read().rstrip()  # remove possíveis \n do final
            f.seek(0)
            f.write(conteudo)
            f.truncate()  # garante que não sobra lixo no fim
    else:
        open(arquivo, "w", encoding="utf-8").close()

    while True:
        nomecharatual = obter_titulo_do_filho(handle_filho)

        if nomecharatual != '1' and nomecharanterior != nomecharatual:
            nomecharanterior = nomecharatual
            print(nomecharatual)

            with open(arquivo, "a", encoding="utf-8") as f:
                if os.path.getsize(arquivo) > 0:
                    f.write("\n")  # separa do último nome já salvo
                f.write(nomecharatual)

        time.sleep(0.5)


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


def listar_e_inspecionar_filhos(handle_pai):
    filhos = []

    def enum_callback(handle, lparam):
        filhos.append(handle)
        return True

    ENUM_CHILD_WINDOWS = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )
    enum_proc = ENUM_CHILD_WINDOWS(enum_callback)
    ctypes.windll.user32.EnumChildWindows(handle_pai, enum_proc, 0)
    return filhos


def obter_titulo_do_filho(handle):
    try:
        WM_GETTEXT = 0x000D
        buffer = ctypes.create_unicode_buffer(512)
        ctypes.windll.user32.SendMessageW(handle, WM_GETTEXT, 512, ctypes.byref(buffer))
        return buffer.value
    except:
        return ""


if __name__ == "__main__":
    main()
