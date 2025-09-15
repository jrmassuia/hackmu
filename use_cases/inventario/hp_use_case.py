from PIL import Image
import pyautogui

from domain.repositories.arduino import Arduino
from interface_adapters.helpers.buscar_localizacao_item_na_tela_manager import BuscarLocalizacaoItemNaTelaManager


class HpUseCase:

    def __init__(self):
        self.arduino_controller = Arduino()

    @staticmethod
    def move_hp_20_para_chaos_machine():
        local_hp_large_20 = HpUseCase.buscar_local_hp_large_20()
        if local_hp_large_20:
            HpUseCase.clicar_no_local_encontrado(local_hp_large_20)
            local_campo_vazio = HpUseCase.buscar_local_campo_vazio_chaos_machine()
            if local_campo_vazio:
                HpUseCase.clicar_no_local_encontrado(local_campo_vazio)
        return local_hp_large_20

    @staticmethod
    def move_hp_15_para_chaos_machine(qtd_hp_para_mover):
        contador = 0
        while contador < qtd_hp_para_mover:
            local_hp_large_15 = HpUseCase.buscar_local_hp_large_15()
            if local_hp_large_15:
                HpUseCase.clicar_no_local_encontrado(local_hp_large_15)
                local_campo_vazio = HpUseCase.buscar_local_campo_vazio_chaos_machine()
                if local_campo_vazio:
                    HpUseCase.clicar_no_local_encontrado(local_campo_vazio)
            else:
                return False
            contador += 1
        return True

    @staticmethod
    def contar_qtd_hp_na_cm():
        path_imagem_hp = Image.open(r'img\hplarge15.jpg')
        pontos_correspondencia = pyautogui.locateAllOnScreen(path_imagem_hp, region=(850, 250, 350, 200),
                                                             confidence=0.84)
        return len(list(pontos_correspondencia))

    @staticmethod
    def buscar_local_hp_large_15():
        return BuscarLocalizacaoItemNaTelaManager.buscar_no_inventario(Image.open(r'static\img\hplarge15.jpg'))

    @staticmethod
    def buscar_local_hp_large_20():
        return BuscarLocalizacaoItemNaTelaManager.buscar_no_inventario(Image.open(r'static\img\hplarge20.jpg'))

    @staticmethod
    def buscar_local_campo_vazio_chaos_machine():
        return pyautogui.locateOnScreen(Image.open(r'static\img\campovazioInteiro.jpg'), region=(850, 250, 350, 200),
                                        confidence=.80)

    @staticmethod
    def clicar_no_local_encontrado(local):
        pyautogui.moveTo(local)
        Arduino().executar_click_esquerdo()
