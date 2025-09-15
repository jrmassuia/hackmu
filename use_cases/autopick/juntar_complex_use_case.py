from datetime import datetime
from PIL import Image
import pyautogui

from domain.repositories.arduino import Arduino
from interface_adapters.helpers.buscar_localizacao_item_na_tela_manager import BuscarLocalizacaoItemNaTelaManager
from interface_adapters.helpers.session_manager import InventarioManager, UpManager
from use_cases.inventario.inventario_use_case import InventarioUseCase
from utils.tela_util import TelaUtil

IMG_COMPLEX_COM_QTD_20 = Image.open(r'static\img\qtd20.jpg')
IMG_COMPLEX_SMALL = Image.open(r'static\img\complexsmallinvetario.jpg')
IMG_COMPLEX_LARGE = Image.open(r'static\img\complexlargeinventario.jpg')
IMG_COMPLEX_MEDIUM = Image.open(r'static\img\complexmediuminventario.jpg')


class JuntarComplexUseCase:
    def __init__(self):
        self.max_segundos_para_juntar = 3600
        self.arduino_controller = Arduino()
        self._executar()

    def _executar(self):
        self._verificar_e_organizar_complexo(None)

    def _verificar_e_organizar_complexo(self, handle):
        if self._deve_organizar_complexo():
            InventarioManager().atualizar_data_hora_organiza_complex(handle)
            self._desativar_up_f8_se_necessario()
            self._organizar_inventario()

    def _deve_organizar_complexo(self):
        ultima_organizacao = InventarioManager.buscar_data_hora_organiza_complex()
        tempo_decorrido = datetime.now() - ultima_organizacao
        return tempo_decorrido.seconds > self.max_segundos_para_juntar

    def _desativar_up_f8_se_necessario(self, handle):
        if UpManager().verifica_se_f8_ativado(handle):
            UpManager.desativar_f8(handle)
            # self.arduino_controller.pressionarF8()

    def _organizar_inventario(self):
        InventarioUseCase.clicar_no_inventario()
        if BuscarLocalizacaoItemNaTelaManager.buscar_no_inventario(Image.open(r'static\img\campovazio.jpg')):
            self._agrupar_itens_complexos()
        self._reposicionar_cursor_e_clicar()

    def _agrupar_itens_complexos(self):
        posicoes_complexos_pequenos, posicoes_complexos_medio, posicoes_complexos_grandes = self._buscar_posicoes_itens_complexos()
        self._agrupar(posicoes_complexos_pequenos, IMG_COMPLEX_COM_QTD_20)
        self._agrupar(posicoes_complexos_medio, IMG_COMPLEX_COM_QTD_20)
        self._agrupar(posicoes_complexos_grandes, IMG_COMPLEX_COM_QTD_20)

    def _buscar_posicoes_itens_complexos(self):
        pos_linha_inicial = 1273
        pos_coluna_inicial = 490
        coluna = None

        posicoes_complexos_pequenos = []
        posicoes_complexos_medio = []
        posicoes_complexos_grandes = []

        for x in range(8):
            linha = pos_linha_inicial
            for y in range(8):
                if coluna is None:
                    coluna = pos_coluna_inicial

                posicao_item = (linha, coluna)
                pyautogui.moveTo(posicao_item)

                item_encontrado = self._verificar_item(
                    InventarioUseCase.buscar_item_dentro_inventario(IMG_COMPLEX_SMALL),
                    posicao_item, posicoes_complexos_pequenos, IMG_COMPLEX_SMALL)
                if not item_encontrado:
                    item_encontrado = self._verificar_item(
                        InventarioUseCase.buscar_item_dentro_inventario(IMG_COMPLEX_LARGE),
                        posicao_item, posicoes_complexos_grandes, IMG_COMPLEX_LARGE)
                if not item_encontrado:
                    self._verificar_item(InventarioUseCase.buscar_item_dentro_inventario(IMG_COMPLEX_MEDIUM),
                                         posicao_item, posicoes_complexos_medio, IMG_COMPLEX_MEDIUM)

                linha += 40
            coluna += 43

        return posicoes_complexos_pequenos, posicoes_complexos_medio, posicoes_complexos_grandes

    def _verificar_item(self, item_encontrado, posicao_item, lista_posicoes, caminho_imagem_item):
        if item_encontrado:
            lista_posicoes.append([posicao_item, caminho_imagem_item])
            return True
        return False

    def _agrupar(self, posicoes_itens, item):
        if posicoes_itens:
            posicao_base_item = None
            for posicao_item, caminho_imagem_item in posicoes_itens:
                pyautogui.moveTo(posicao_item)
                if InventarioUseCase.buscar_item_dentro_inventario(item) is None:
                    if posicao_base_item is None:
                        posicao_base_item = posicao_item
                    else:
                        self._realizar_agrupar(posicao_base_item, posicao_item, caminho_imagem_item, item)
                        posicao_base_item = posicao_item

    def _realizar_agrupar(self, posicao_base, posicao_atual, caminho_imagem_item, caminho_maximo_quantidade):
        self.arduino_controller.executar_click_esquerdo()
        pyautogui.moveTo(posicao_base)
        self.arduino_controller.executar_click_esquerdo()
        pyautogui.moveTo(posicao_atual)

        if InventarioUseCase.buscar_item_dentro_inventario(caminho_maximo_quantidade) is None and \
                InventarioUseCase.buscar_item_dentro_inventario(caminho_imagem_item):
            posicao_base = posicao_atual

    def _reposicionar_cursor_e_clicar(self):
        TelaUtil().centroTela()
        InventarioUseCase.clicar_no_inventario()
        TelaUtil().centroTela()
