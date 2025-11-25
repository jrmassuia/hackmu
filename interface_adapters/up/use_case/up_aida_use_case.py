import time

import win32gui

from interface_adapters.up.up_util.up_util import Up_util
from services.posicionamento_spot_service import PosicionamentoSpotService
from sessao_handle import get_handle_atual
from use_cases.autopick.pegar_item_use_case import PegarItemUseCase
from utils import mouse_util, spot_util, safe_util
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.teclado_util import Teclado_util


class UpAidaUseCaseNovo:
    def __init__(self):
        self.handle = get_handle_atual()
        self.mover_spot_util = MoverSpotUtil()
        self.tela = win32gui.GetWindowText(self.handle)
        self.pointer = Pointers()
        self.up_util = Up_util()
        self.auto_pick = PegarItemUseCase(self.handle)
        self.teclado_util = Teclado_util()
        self.classe = self.pointer.get_classe()

        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0
        self.ja_moveu_para_aida = False
        self.up_liberado = False
        self.coord_spot_atual = None
        self.coord_mouse_atual = None

    def executar(self):
        if not self.ja_moveu_para_aida:
            if not self.verficar_se_char_ja_esta_spot():
                self.teclado_util.escrever_texto('/move aida2')
                time.sleep(2)
                self._posicionar_char_spot()
            self.ja_moveu_para_aida = True

        if self.up_liberado:
            if safe_util.aida(self.handle):
                self.ja_moveu_para_aida = False
                print('Esperando na safe de aida por 120s')
                time.sleep(120)  # ESPERA PRA VOLTAR PRO SPOT
            else:
                self.auto_pick.execute()
                self.limpar_mob_ao_redor()
                self._ativar_skill()
                self._corrigir_coordenada_e_mouse()

        return self.up_liberado

    def verficar_se_char_ja_esta_spot(self):
        posiconamento_service = PosicionamentoSpotService(spot_util.buscar_todos_spots_aida())

        if posiconamento_service.verficar_se_char_ja_esta_spot():
            self.coord_mouse_atual = posiconamento_service.get_coord_mouse()
            self.coord_spot_atual = posiconamento_service.get_coord_spot()
            return True
        return False

    def _posicionar_char_spot(self, iniciar_por_aida_2=True):
        if iniciar_por_aida_2:
            spots = spot_util.buscar_spots_aida_2()
        else:
            spots = spot_util.buscar_spots_aida_1()

        poscionar = PosicionamentoSpotService(spots)

        achou_spot = poscionar.posicionar_bot_up()

        if not iniciar_por_aida_2 and not achou_spot:
            # Se não achou em Aida 1, espera e tenta subir pra Aida 2
            time.sleep(1200)
            self.mover_spot_util.movimentar(
                (207, 169),
                max_tempo=3600,
                limpar_spot_se_necessario=True,
                movimentacao_proxima=True
            )
            self._posicionar_char_spot()  # Volta a procurar em Aida 2
            return  # Impede de continuar com os dados antigos

        if not achou_spot:
            # Se não achou em Aida 2, tenta Aida 1
            self.teclado_util.escrever_texto('/move aida')
            time.sleep(2)
            self._sair_da_safe()
            self._posicionar_char_spot(iniciar_por_aida_2=False)
            return  # Impede de continuar com os dados antigos

        # Se encontrou o spot, atualiza as coordenadas
        if achou_spot:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()
            self.up_liberado = True
        else:
            self.up_liberado = False

    def limpar_mob_ao_redor(self):
        self.tempo_inicial_limpar_mob_ao_redor = self.up_util.limpar_mob_ao_redor(
            self.tempo_inicial_limpar_mob_ao_redor, self.classe)

    def _ativar_skill(self):
        self.tempo_inicial_ativar_skill = self.up_util.ativar_skill(self.classe, self.tempo_inicial_ativar_skill)

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar(self.coord_spot_atual,
                                            verficar_se_movimentou=True)
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _sair_da_safe(self):
        self.mover_spot_util.movimentar((100, 10), movimentacao_proxima=True)
