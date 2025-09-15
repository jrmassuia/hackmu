import pyautogui

TELA_CENTRO = 'CENTRO'
TELA_INTEIRA = 'INTEIRA'
TELA_INVENTARIO = 'INVENTARIO'
TELA_BAU = 'BAU'

posix1 = 400
posiy1 = 60
posix2 = 1000
posiy2 = 900


class BuscarLocalizacaoItemNaTelaManager:

    @staticmethod
    def buscar_em_toda_tela(pathImagem):
        return pyautogui.locateOnScreen(pathImagem, confidence=.80)

    @staticmethod
    def buscar_centro_tela(pathImagem):
        return pyautogui.locateOnScreen(pathImagem, region=(posix1, posiy1, posix2, posiy2), confidence=.80)

    @staticmethod
    def buscar_no_inventario(pathImagem):
        return pyautogui.locateOnScreen(pathImagem, region=(1230, 460, 350, 350), confidence=.80)

    @staticmethod
    def buscar_no_bau(pathImagem):
        return pyautogui.locateOnScreen(pathImagem, region=(840, 140, 360, 650), confidence=.80)
