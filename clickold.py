import win32gui
import win32api
import win32con
import time

def make_long(x, y):
    return win32api.MAKELONG(x, y)

handle = win32gui.FindWindow(None, "[3/3] MUCABRASIL - NVIDIA GeForce GTX 1050 Ti/PCIe/SSE2 - Rota Illusion66")

if handle == 0:
    print("Janela não encontrada.")
else:
    # Coordenadas desejadas dentro da janela
    x, y = 519, 594

    position = make_long(x, y)

    # Move o mouse para a posição
    win32gui.PostMessage(handle, win32con.WM_MOUSEMOVE, 0, position)
    time.sleep(0.1)
    # Clique do mouse
    win32gui.PostMessage(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, None)
    time.sleep(0.1)
    win32gui.PostMessage(handle, win32con.WM_LBUTTONUP, None, None)


# Função de callback para cada janela
# def enum_window_callback(hwnd, windows):
#     if win32gui.IsWindowVisible(hwnd):  # Verifica se a janela está visível
#         window_text = win32gui.GetWindowText(hwnd)  # Obtém o texto da janela
#         if window_text:  # Apenas inclui janelas com título
#             windows.append((hwnd, window_text))
#
# # Lista para armazenar as janelas
# windows = []
#
# # Enumera todas as janelas
# win32gui.EnumWindows(enum_window_callback, windows)
#
# # Exibe todas as janelas
# for hwnd, window_text in windows:
#     print(f"Handle: {hwnd}, Título: {window_text}")