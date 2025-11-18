import time

import win32gui

from utils import mouse_util
from utils.mover_spot_util import MoverSpotUtil


def _mover_k3(handle):
    while True:
        chegou = MoverSpotUtil(handle).movimentar((82, 91), max_tempo=600, movimentacao_proxima=True,
                                                              limpar_spot_se_necessario=True)
        if chegou:
            break
    mouse_util.mover(handle, 490, 338)
    mouse_util.ativar_click_esquerdo(handle)
    time.sleep(3)
    mouse_util.desativar_click_esquerdo(handle)


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
    mouse_util.zoonTela(handle)
    _mover_k3(handle)


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
