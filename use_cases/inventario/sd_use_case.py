import time
import pyautogui
from PIL import Image

from domain.repositories.arduino import Arduino
from interface_adapters.helpers.buscar_localizacao_item_na_tela_manager import BuscarLocalizacaoItemNaTelaManager
from interface_adapters.helpers.session_manager import BauManager


class SdUseCase:
    @staticmethod
    def mover_sd_para_inventario():
        tempo_maximo = 1.5
        tempo_decorrido = 0.0
        while tempo_decorrido < tempo_maximo:
            time.sleep(.15)
            local_sd_chaos_machine = SdUseCase.buscar_local_sd_10_chaos_machine()
            if local_sd_chaos_machine:
                SdUseCase.clicar_no_local_encontrado(local_sd_chaos_machine)
                local_campo_vazio = SdUseCase.buscar_local_campo_vazio_inventario()
                if local_campo_vazio:
                    SdUseCase.clicar_no_local_encontrado(local_campo_vazio)
                    break
            tempo_decorrido += 0.15
        SdUseCase.fechar_inventario()

    @staticmethod
    def mover_sd_para_bau():
        img_sd = Image.open(r'img\sd10.jpg')
        muda_bau = False
        while True:
            if muda_bau:
                SdUseCase.atualizar_bau()
            sds_inventario = pyautogui.locateAllOnScreen(img_sd, region=(1230, 460, 350, 350), confidence=.88)
            for sd in sds_inventario:
                pyautogui.moveTo(sd)
                # Arduino().executar_click_direito()
            local_sd_inventario = SdUseCase.buscar_local_sd_10_inventario()
            if local_sd_inventario:
                muda_bau = True
            else:
                break
        SdUseCase.fechar_inventario()

    @staticmethod
    def buscar_local_sd_10_chaos_machine():
        path_imagem_sd_10 = Image.open(r'img\sd10.jpg')
        return pyautogui.locateOnScreen(path_imagem_sd_10, region=(850, 250, 350, 200), confidence=.80)

    @staticmethod
    def buscar_local_sd_10_inventario():
        return BuscarLocalizacaoItemNaTelaManager.buscar_no_inventario(Image.open(r'static\img\sd10.jpg'))

    @staticmethod
    def buscar_local_campo_vazio_inventario():
        return BuscarLocalizacaoItemNaTelaManager.buscar_no_inventario(Image.open(r'static\img\campovazio.jpg'))

    @staticmethod
    def fechar_inventario():
        pyautogui.moveTo(1280, 910)
        Arduino().executar_click_esquerdo()

    @staticmethod
    def atualizar_bau():
        for bau in range(21):
            bau_atual = BauManager.buscar_bau_atual()
            numero_bau_atual = int(bau_atual[-2:])
            if bau > numero_bau_atual and str(bau) not in bau_atual:
                SdUseCase.fechar_inventario()
                BauManager.atualizar_bau(str(bau))
                Arduino().comunicar_com_arduino(BauManager.buscar_bau_atual())
                time.sleep(12)  # Tempo para alterar o baú
                break
            elif str(20) in bau_atual:
                exit()
        SdUseCase.clicar_no_bau()

    @staticmethod
    def clicar_no_bau():
        pyautogui.moveTo(950, 400)
        time.sleep(1)
        Arduino().executar_click_esquerdo()

    @staticmethod
    def clicar_no_local_encontrado(local):
        pyautogui.moveTo(local)
        Arduino().executar_click_esquerdo()
