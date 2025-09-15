import re
import win32con
import win32gui
import win32ui
from PIL import Image
import cv2
import numpy as np
from pytesseract import pytesseract

pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# Função para capturar a tela da janela sem bordas
def capture_window(handle):
    try:
        # Obtém as coordenadas da janela (inclui bordas)
        left, top, right, bottom = win32gui.GetWindowRect(handle)

        # Obtém o retângulo da área cliente (sem bordas)
        client_rect = win32gui.GetClientRect(handle)

        # Calcula a posição da área cliente em relação à janela inteira
        client_width = client_rect[2]
        client_height = client_rect[3]
        border_left, border_top = win32gui.ClientToScreen(handle, (0, 0))

        # Calcula o deslocamento em relação ao canto superior esquerdo
        left_offset = border_left - left
        top_offset = border_top - top

        # Captura somente a área útil (sem bordas)
        hwndDC = win32gui.GetWindowDC(handle)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, client_width, client_height)

        saveDC.SelectObject(saveBitMap)

        # Copia a tela da área cliente para o bitmap
        saveDC.BitBlt((0, 0), (client_width, client_height), mfcDC, (left_offset, top_offset), win32con.SRCCOPY)

        # Converte para PIL Image
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)

        # Salva o screenshot, se o caminho for fornecido
        # if save_path:
        #     img.save(save_path)
        #     print(f"Screenshot salvo em: {save_path}")

        # Libera os objetos
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(handle, hwndDC)

        return img
    except:
        return None


def capture_region(handle, x, y, width, height):
    # Captura a área desejada da janela, iniciando em (x, y) e com as dimensões especificadas
    hwndDC = win32gui.GetWindowDC(handle)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)

    # Copia a área especificada da janela para o bitmap
    saveDC.BitBlt((0, 0), (width, height), mfcDC, (x, y), win32con.SRCCOPY)

    # Converte para PIL Image
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)

    # Libera os recursos
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(handle, hwndDC)

    save_path = "region_capture2.png"
    # if save_path:
    #     img.save(save_path)
    #     print(f"Screenshot salvo em: {save_path}")

    return img


import cv2
import numpy as np
from PIL import Image

def is_image_in_region(region_img, template_img_path, threshold=0.87):

    if isinstance(region_img, str):
        region_img = Image.open(region_img)

    # Converte a imagem da região (PIL) para OpenCV (grayscale)
    region_cv = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2GRAY)

    # Carrega a imagem template e também converte para grayscale
    template_cv = cv2.imread(template_img_path, cv2.IMREAD_GRAYSCALE)

    if template_cv is None:
        print(f"Erro ao carregar a imagem: {template_img_path}")
        return False

    # Faz o template matching com imagens em escala de cinza
    result = cv2.matchTemplate(region_cv, template_cv, cv2.TM_CCOEFF_NORMED)

    # Encontra o valor máximo de correspondência
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # Verifica se passou do limiar
    if max_val >= threshold:
        # print(f"Imagem encontrada com {max_val * 100:.2f}% de correspondência nas coordenadas {max_loc}.")
        return True
    else:
        # print(f"Imagem não encontrada. Melhor correspondência: {max_val * 100:.2f}%.")
        return False



def capture_specific_region(handle, region_x, region_y, region_width, region_height):
    # Captura a região especificada da janela e salva o screenshot
    img = capture_region(handle, region_x, region_y, region_width, region_height)
    # Exibe a imagem capturada
    # img.show()
