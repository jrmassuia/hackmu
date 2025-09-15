import time
from datetime import datetime

from interface_adapters.helpers.session_manager_new import *
from utils import acao_menu_util, mover_char_util, mouse_util, converter_util
from utils.buscar_item_util import BuscarItemUtil
from utils.teclado_util import Teclado_util


class GuardarItemNoBauUseCase:

    def __init__(self, handle, conexao_arduino, mapa):
        self.handle = handle
        self.mapa = mapa
        self.sessao = Sessao(handle=handle)
        self.teclado_util = Teclado_util(self.handle, conexao_arduino)
        self._execute()

    def _execute(self):
        atingiuTempo = self._verifica_se_atingiu_tempo_limite()
        if atingiuTempo:
            # InventarioManager.atualizar_data_hora_guardou_item_no_bau(self.handle)
            self.sessao.atualizar_inventario(InventarioFields.DATA_HORA_GUARDOU_ITEM_NO_BAU, datetime.now().isoformat())
            acao_menu_util.clicar_inventario(self.handle)
            time.sleep(.5)
            # itens = buscar_item_util.buscar_itens(self.handle, './static/guardar_bau')
            itens = BuscarItemUtil(self.handle).buscar_varios_itens('./static/guardar_bau')
            self._guardar_item_bau(itens)

    def _verifica_se_atingiu_tempo_limite(self):
        # InventarioManager.atualizar_visualizar_inventario(self.handle, 'SIM')
        self.sessao.atualizar_inventario(InventarioFields.VISUALIZAR, 'SIM')
        # datahora = InventarioManager.buscar_data_hora_guardou_item_no_bau(self.handle)
        datahora = converter_util.stringToDateTime(
            self.sessao.ler_inventario(InventarioFields.DATA_HORA_GUARDOU_ITEM_NO_BAU))
        horaAtual = datetime.now()
        calcTempo = horaAtual - datahora
        return calcTempo.seconds > 120

    def _guardar_item_bau(self, itens):
        achou = False
        if itens:
            # AutoPickManager.atualizar_autopick_inicial(self.handle)
            self.sessao.atualizar_autopick(AutopickFields.INICIOU_AUTOPICK, 'NAO')
            for item in itens:
                if item[2] in 'gemstone':
                    self._guardar(itens)
                    achou = True
                    break

        if achou is False:
            acao_menu_util.clicar_inventario(self.handle)

    def _guardar(self, itens):
        # self._desativar_up()
        self._mover_para_lost_tower()
        movimentou = self._movimentar_para_bau()
        if movimentou:
            mouse_util.clickEsquerdo(self.handle)
            time.sleep(1)
            for item in itens:
                mouse_util.right_clique(self.handle, item[0] + 8, item[1] + 8)
            acao_menu_util.clicar_inventario(self.handle)

        if self.mapa == 'k1':
            self.teclado_util.escrever_texto('/move kanturu')
        elif self.mapa == 'k3':
            self.teclado_util.escrever_texto('/move kanturu3')

    def _desativar_up(self):
        # if (UpManager.verifica_se_f8_ativado(self.handle)):
        if self.sessao.ler_up(UpFields.F8_PRESSIONADO) == 'SIM':
            # UpManager.desativar_f8(self.handle)
            self.sessao.atualizar_up(UpFields.F8_PRESSIONADO, 'NAO')
            mouse_util.desativar_click_direito(self.handle)

    def _mover_para_lost_tower(self):
        self.teclado_util.escrever_texto('/move losttower')
        time.sleep(2)

    def _movimentar_para_bau(self):
        movimentou = self._primeira_tentativa_movimentacao()
        if movimentou is False:
            self._mover_para_lost_tower()
            movimentou = self._segunda_tentativa_movimentacao()
        if movimentou is False:
            self._mover_para_lost_tower()
            movimentou = self._terceira_tentativa_movimentacao()
        if movimentou is False:
            self._mover_para_lost_tower()
            self._quarta_tentativa_movimentacao()
        time.sleep(3)
        return movimentou

    def _primeira_tentativa_movimentacao(self):
        coodenadas = (201, 77)
        return self._movimentar(coodenadas, 370, 186)

    def _segunda_tentativa_movimentacao(self):
        coodenadas = (202, 77)
        return self._movimentar(coodenadas, 340, 170)

    def _terceira_tentativa_movimentacao(self):
        coodenadas = (203, 77)
        return self._movimentar(coodenadas, 320, 150)

    def _quarta_tentativa_movimentacao(self):
        coodenadas = (204, 77)
        return self._movimentar(coodenadas, 300, 135)

    def _movimentar(self, coodenadas, x, y):
        movimentou = mover_char_util.mover(self.handle, coodenadas, 8)
        if movimentou:
            mouse_util.mover(self.handle, x, y)
        return movimentou
