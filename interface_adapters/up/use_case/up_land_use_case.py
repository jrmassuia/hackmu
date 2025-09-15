import time

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from services.posicionamento_spot_service import PosicionamentoSpotService
from use_cases.autopick.pegar_item_use_case import PegarItemUseCase
from utils import mouse_util, spot_util, safe_util
from utils.buscar_item_util import BuscarItemUtil
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.teclado_util import Teclado_util


class UpLandUseCase:
    def __init__(self, handle, conexao_arduino):
        self.handle = handle
        self.sessao = Sessao(handle=handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)
        self.auto_pick = PegarItemUseCase(self.handle, conexao_arduino)
        self.pointer = Pointers(self.handle)
        self.mover_spot_util = MoverSpotUtil(handle)
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=conexao_arduino)
        self.teclado_util = Teclado_util(self.handle, conexao_arduino)
        self.ja_moveu_para_loren = False
        self.coord_spot_atual = None
        self.coord_mouse_atual = None
        self.up_liberado = False
        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0
        self.tentativa_up_land = 0

    def executar(self):
        return self._mover_para_loren()

    def _mover_para_loren(self):
        if safe_util.lorencia(self.handle):
            self.ja_moveu_para_loren = False
            time.sleep(2)

        if not self.ja_moveu_para_loren:
            self.teclado_util.escrever_texto('/move loren')
            time.sleep(2)
            self.ja_moveu_para_loren = True
            self.mover_spot_util.movimentar_loren((93, 49))
            self.mover_spot_util.movimentar_loren((93, 89), movimentacao_proxima=True)
            self._entrar_em_land()

            entrada_nao_permitida = self._entrada_nao_permitida()
            if entrada_nao_permitida is False:
                return False

            self._ir_ate_inicio_up()
            self._movimentar_em_land()

        self.auto_pick.execute()
        self.limpar_mob_ao_redor()
        self._ativar_skill()
        self._corrigir_coordenada_e_mouse()

        return self.up_liberado

    def _entrar_em_land(self):
        movimentou = self.mover_spot_util.movimentar_loren((140, 94), verficar_se_movimentou=True)
        if movimentou:
            mouse_util.left_clique(self.handle, 597, 55)  # clica guarda
            time.sleep(3)
        else:
            movimentou = self.mover_spot_util.movimentar_loren((145, 95), verficar_se_movimentou=True)
            if movimentou:
                mouse_util.left_clique(self.handle, 377, 18)  # clica guarda
                time.sleep(5)

        mouse_util.left_clique(self.handle, 681, 143)  # clica entrar
        time.sleep(3)

    def _entrada_nao_permitida(self):
        mouse_util.mover(self.handle, 1, 1)
        entrada_nao_permitida = BuscarItemUtil(self.handle).buscar_item_simples('./static/img/landnaopermitido.png')
        if entrada_nao_permitida is not None:
            mouse_util.left_clique(self.handle, 16, 527, delay=1)
            return False
        return True

    def _movimentar_em_land(self):
        self.teclado_util.selecionar_skill_1()
        self.teclado_util.pressionar_zoon()
        return self._posicionar_em_spot_adequado()

    def _ir_ate_inicio_up(self):
        movimentou = self.mover_spot_util.movimentar_land(
            (92, 82),
            max_tempo=300,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            movimentacao_proxima=True
        )

        if not movimentou:
            print("Não foi possível se mover até o local. Encerrando movimentação.")
            return False
        else:
            return True

    def _posicionar_em_spot_adequado(self):
        spots = spot_util.buscar_spots_land()
        poscionar = PosicionamentoSpotService(self.handle, self.pointer, self.mover_spot_util, self.classe, None, spots,
                                              PathFinder.MAPA_LAND)

        achou = poscionar.posicionar_bot_up()
        if achou:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()
            self.teclado_util.escrever_texto("/autopick on")

            if self.pointer.get_nome_char() == 'Layna_':
                self.teclado_util.escrever_texto("/autodc 23:59 Rafael - CS Blacked 400")
            elif self.pointer.get_nome_char() == 'DL_DoMall':
                self.teclado_util.escrever_texto("/autodc 23:59 Romualdo BLEKALT_EF 400")
            elif self.pointer.get_nome_char() == 'ReiDav1':
                self.teclado_util.escrever_texto("/autodc 23:59 Vinny Rocha TH 400")
            else:
                self.teclado_util.escrever_texto("/autodc 23:59 Romualdo TH 400")

            self.up_liberado = True
        else:
            self.tentativa_up_land = self.tentativa_up_land + 1
            print(
                self.pointer.get_nome_char() + ' - Tentativa de encontrar spot em land: ' + str(self.tentativa_up_land))

            if self.tentativa_up_land > 3:
                self.up_liberado = False
            else:
                self._ir_ate_inicio_up()
                time.sleep(300)
                self._movimentar_em_land()

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar_land(self.coord_spot_atual,
                                                 verficar_se_movimentou=True)
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def limpar_mob_ao_redor(self):
        self.tempo_inicial_limpar_mob_ao_redor = self.up_util.limpar_mob_ao_redor(
            self.tempo_inicial_limpar_mob_ao_redor, self.classe)

    def _ativar_skill(self):
        self.tempo_inicial_ativar_skill = self.up_util.ativar_skill(self.classe, self.tempo_inicial_ativar_skill)
