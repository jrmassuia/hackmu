from PIL import Image
import pyautogui
import time

from domain.repositories.arduino import Arduino


class InventarioUseCase:

    @staticmethod
    def abrir_inventario():
        local_inventario = pyautogui.locateOnScreen(Image.open(r'static\img\inventario.png'), confidence=.80)
        if local_inventario:
            pyautogui.moveTo(local_inventario)
            time.sleep(0.05)
            Arduino().executar_click_esquerdo()
            time.sleep(0.05)

    @staticmethod
    def fechar_inventario():
        pyautogui.moveTo(1280, 910)
        Arduino().executar_click_esquerdo()

    @staticmethod
    def clicar_no_inventario():
        pyautogui.moveTo(1170, 1020)
        time.sleep(.5)
        Arduino().executar_click_esquerdo()
        time.sleep(.5)

    @staticmethod
    def buscar_item_dentro_inventario(imagem):
        return pyautogui.locateOnScreen(imagem, region=(1190, 350, 420, 480), confidence=.80)
