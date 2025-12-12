import time

import win32gui

from interface_adapters.controller.BaseController import BaseController
from interface_adapters.up.up_util.up_util import Up_util
from menu import Menu
from sessao_menu import obter_menu
from use_cases.autopick.pegar_item_use_case import PegarItemUseCase
from utils import buscar_coordenada_util, mouse_util, safe_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class AutopickController(BaseController):

    def _prepare(self):
        self.mover_spot_util = MoverSpotUtil()
        self.tela = win32gui.GetWindowText(self.handle)
        self.auto_pick = PegarItemUseCase(self.handle)
        self.pointer = Pointers()
        self.up_util = Up_util()
        self.teclado_util = Teclado_util()

        self.executando = True  # Variável de controle para o loop
        self.iniciou_autopick = False
        self.x_coordenda_autal = self.pointer.get_cood_x()
        self.y_coordenda_autal = self.pointer.get_cood_y()

    def _run(self):
        try:
            if obter_menu(self.handle).get(Menu.ATIVO) == 1:
                self._processar_autopick_geral()
            else:
                print(f"AutoPick desativado para a tela {self.handle}.")
        except Exception as e:
            print(f"Erro na tela {self.handle}: {e}")
            raise  # Relança a exceção para que o MainApp possa tratar

    def _enviar_comando_inicial(self):
        self.teclado_util.escrever_texto('/re off')
        time.sleep(.5)
        self.teclado_util.escrever_texto('/autopick on')
        time.sleep(.5)

    def _processar_autopick_geral(self):
        while self.executando:
            if self._esta_na_safe_aida():
                self._mover_para_spot_aida()
            elif safe_util.k3(self.handle):
                self._mover_para_spot_k3()
            elif safe_util.atlans(self.handle):
                self._mover_para_spot_atlans()
            self._voltar_para_k3_se_necessario()
            self.auto_pick.execute()

            self.up_util.ativar_desc_item_spot()

    def _mover_para_spot_aida(self):
        if self._esta_na_safe_aida():
            if self.iniciou_autopick:
                time.sleep(60)
            else:
                self.iniciou_autopick = True

            self._sair_da_safe_aida()

        if '[1/3]' in self.tela:
            coordenada = (226, 12)

        elif '[2/3]' in self.tela:
            coordenada = (151, 37)
        else:
            coordenada = (205, 171)

        self.mover_spot_util.movimentar(coordenada,
                                        max_tempo=400,
                                        limpar_spot_se_necessario=True,
                                        verficar_se_movimentou=True)

    def _mover_para_spot_k3(self):
        if self.iniciou_autopick:
            time.sleep(300)
        else:
            self.iniciou_autopick = True

        safe_util.sair_da_safe_k3(self.mover_spot_util)
        if '[1/3]' in self.tela:
            coordenada = (167, 94)
        elif '[2/3]' in self.tela:
            coordenada = (108, 143)
        else:
            coordenada = (165, 129)

        self.mover_spot_util.movimentar(coordenada,
                                        max_tempo=180,
                                        limpar_spot_se_necessario=True,
                                        movimentacao_proxima=True,
                                        verficar_se_movimentou=True)

    def _voltar_para_k3_se_necessario(self):
        ycood, xcood = buscar_coordenada_util.coordernada(self.handle)
        if (xcood and ycood) and ((85 <= xcood <= 95) and (80 <= ycood <= 90)):
            while True:
                chegou = MoverSpotUtil().movimentar((82, 91), max_tempo=600,
                                                    movimentacao_proxima=True,
                                                    limpar_spot_se_necessario=True)
                if chegou:
                    break
            mouse_util.mover(self.handle, 490, 338)
            mouse_util.ativar_click_esquerdo(self.handle)
            time.sleep(3)
            mouse_util.desativar_click_esquerdo(self.handle)

    def _mover_para_spot_atlans(self):
        time.sleep(300)
        safe_util.sair_da_safe_atlans(self.mover_spot_util)
        self.mover_spot_util.movimentar((self.y_coordenda_autal, self.x_coordenda_autal),
                                        limpar_spot_se_necessario=True,
                                        movimentacao_proxima=True)

    def _esta_na_safe_aida(self):
        ycood, xcood = buscar_coordenada_util.coordernada(self.handle)
        return (xcood and ycood) and ((5 <= xcood <= 17) and (75 <= ycood <= 92))

    def _esta_na_safe_k3(self):
        ycood, xcood = buscar_coordenada_util.coordernada(self.handle)
        return (xcood and ycood) and ((100 <= xcood <= 110) and (70 <= ycood <= 77))

    def _sair_da_safe_aida(self):
        self.mover_spot_util.movimentar((100, 10), movimentacao_proxima=True)
