import numpy as np
import pyautogui
import win32con
import win32gui
import win32ui
from PIL import Image


class TelaUtil:

    @staticmethod
    def centroTela():
        width, height = pyautogui.size()
        height = (height / 2)
        height = height
        width = width / 2
        pyautogui.moveTo(width, height - 40)

    def capturar_regiao(handle, x, y, largura, altura):
        # Captura uma região da janela especificada pelo handle
        hwnd_dc = win32gui.GetWindowDC(handle)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, largura, altura)
        save_dc.SelectObject(bitmap)
        save_dc.BitBlt((0, 0), (largura, altura), mfc_dc, (x, y), win32con.SRCCOPY)

        # Converte para uma imagem PIL
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        # Libera recursos
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(handle, hwnd_dc)

        return img

    def verificar_cores_na_regiao(handle, x, y, largura, altura, cores_procuradas):
        # Captura a região da tela e converte para um array numpy
        img = capturar_regiao(handle, x, y, largura, altura)
        img_np = np.array(img)

        # Verifica se algum pixel na região corresponde às cores desejadas
        for cor in cores_procuradas:
            r, g, b = cor
            mask = (img_np[:, :, 0] == r) & (img_np[:, :, 1] == g) & (img_np[:, :, 2] == b)
            if mask.any():
                return True
        return False

    # Configurações
    handle = 123456  # Substitua pelo handle da janela desejada
    x, y, largura, altura = 100, 100, 200, 200  # Região a ser capturada
    cores_procuradas = [
        (255, 255, 255),  # Branco (exemplo)
        (0, 255, 255),  # Ciano (exemplo)
        (255, 165, 0)  # Laranja (exemplo)
    ]

    # Executa a verificação
    resultado = verificar_cores_na_regiao(handle, x, y, largura, altura, cores_procuradas)
    print("Cor encontrada:", resultado)

