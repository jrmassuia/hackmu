import numpy as np
import win32con
import win32gui
import win32ui
from PIL import Image


class RegionColorDetector:
    def __init__(self, handle, region, colors):
        """
        Inicializa o detector de cores na região de uma janela.

        :param handle: Identificador da janela (handle).
        :param region: Região de captura na janela (x, y, largura, altura).
        :param colors: Lista de cores RGB a serem detectadas [(r, g, b), ...].
        """
        self.handle = handle
        self.region = region # (250, 150, 300, 300)  # (x, y, largura, altura)
        self.colors = colors

        #[     (102, 178, 255),  # Ciano
        #     (255, 127, 51)  # Laranja
        #     # (255, 204, 25)  # Amarelo
        # ]  # Lista de cores RGB [(r, g, b), ...]

    def _capture_region(self, save_path="region.png"):
        """
        Captura a região da tela especificada e retorna uma imagem PIL.
        Opcionalmente, salva a imagem capturada em um arquivo.

        :param save_path: Caminho para salvar a imagem capturada. Se None, não salva.
        :return: Imagem PIL capturada.
        """
        x, y, largura, altura = self.region
        hwnd_dc = win32gui.GetWindowDC(self.handle)
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

        # Salva a imagem, se um caminho for fornecido
        if save_path:
            img.save(save_path)
            print(f"Imagem capturada salva em {save_path}")

        # Libera recursos
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.handle, hwnd_dc)

        return img

    def detect_colors(self, save_path=None):
        """
        Verifica se alguma das cores especificadas está presente na região capturada.
        Opcionalmente, salva a imagem capturada.

        :param save_path: Caminho para salvar a imagem capturada. Se None, não salva.
        :return: True se alguma das cores for encontrada, False caso contrário.
        """
        img = self._capture_region(save_path=save_path)
        img_np = np.array(img)

        for color in self.colors:
            r, g, b = color
            mask = (img_np[:, :, 0] == r) & (img_np[:, :, 1] == g) & (img_np[:, :, 2] == b)
            if mask.any():
                return True
        return False