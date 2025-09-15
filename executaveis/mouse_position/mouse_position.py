import time

import pyautogui
import win32gui


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
    while True:
        try:
            client_x, client_y, _, _ = get_client_rect_by_handle(handle)
            mouse_x, mouse_y = pyautogui.position()
            relative_x = mouse_x - client_x
            relative_y = mouse_y - client_y

            print(f"Posição do Mouse na Área Cliente da Janela: X={relative_x}, Y={relative_y}")
            time.sleep(0.8)  # Pequeno delay para evitar uso excessivo de CPU
        except KeyboardInterrupt:
            print("Monitoramento encerrado.")
            break


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


def get_client_rect_by_handle(hwnd):
    rect = win32gui.GetClientRect(hwnd)
    point = win32gui.ClientToScreen(hwnd, (0, 0))
    x, y = point
    width, height = rect[2], rect[3]
    return x, y, width, height  # Retorna a posição e tamanho da área cliente da janela


if __name__ == "__main__":
    main()
