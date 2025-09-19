import random
import socket
import time
from datetime import datetime, timedelta

import win32gui

from interface_adapters.helpers.session_manager_new import Sessao, GenericoFields
from interface_adapters.up.up_util.up_util import Up_util
from services.guardar_gem_bau_service import GuardaGemstoneService
from services.movimentar_inicial_bot_k1_k2 import MovimentacaoInicialBotK1k2Service
from services.movimentar_volta_k3_para_k2_service import MovimentacaoVotaK3ParaK2Service
from services.posicionamento_spot_service import PosicionamentoSpotService
from use_cases.autopick.pegar_item_use_case import PegarItemUseCase
from utils import mouse_util, spot_util, safe_util, limpar_mob_ao_redor_util
from utils.gem_no_spot_util import GemNoSpotUtil
from utils.mover_spot_util import MoverSpotUtil
from utils.pointer_util import Pointers
from utils.rota_util import PathFinder
from utils.selecionar_char_util import SelecionarCharUtil
from utils.teclado_util import Teclado_util


class PickKanturuUseCase:
    def __init__(self, handle, arduino):
        # Inicialização de atributos básicos
        self.handle = handle
        self.arduino = arduino
        self.teclado_util = Teclado_util(self.handle, arduino)
        self.tela = win32gui.GetWindowText(self.handle)

        # Sessão e dados do personagem
        self.sessao = Sessao(handle=handle)
        self.classe = self.sessao.ler_generico(GenericoFields.CLASSE_PERSONAGEM)

        # Utilitários relacionados ao movimento e apontadores
        self.mover_spot_util = MoverSpotUtil(self.handle)
        self.pointer = Pointers(self.handle)
        self.up_util = Up_util(self.handle, pointer=self.pointer, conexao_arduino=arduino)

        # Tempos iniciais para controles diversos
        self.tempo_inicial_gem = time.time()
        self.tempo_inicial_pick = time.time()
        self.tempo_inicial_corrigir_coordenada_e_mouse = 120
        self.tempo_inicial_limpar_mob_ao_redor = 0
        self.tempo_inicial_ativar_skill = 0

        # Estado do personagem e controle de ações
        self.mortes = []
        self.coord_spot_atual = None
        self.coord_mouse_atual = None
        self.chegou_spot = False
        self.iniciou_up = False
        self.senha = None

        # Flags de movimentação e objetivos
        self.subir_k3 = False

        # Definir spot de up inicial
        self.spot_up = self._definir_spot_up()

    def execute(self):
        self._definir_comando_inicial()
        auto_pick = PegarItemUseCase(self.handle, self.arduino)

        print('PC - ' + socket.gethostname() + f' - Iniciando bot - {self.tela}')

        while True:
            self._mover_mapa()
            auto_pick.execute()
            self._guardar_gem_no_inventario_se_necessario()
            self.limpar_mob_ao_redor()
            self._ativar_skill()
            self._corrigir_coordenada_e_mouse()  ## SEMPRE DEIXAR POR UTILMO PRA ATIVAR UP
            mouse_util.ativar_click_direito(self.handle)
            self.up_util.ativar_desc_item_spot()

    def _definir_spot_up(self):
        if 'PC1' in socket.gethostname():
            spots_por_tela = [['[1/3]', 12, ''], ['[2/3]', 10, ''], ['[3/3]', 7, '9876Sonso']]
        elif 'PC2' in socket.gethostname():
            spots_por_tela = [['[1/3]', 3, ''], ['[2/3]', 8, ''], ['[3/3]', 9, '']]
        else:
            spots_por_tela = [['[1/3]', 4, 'MGPK2025PK'], ['[2/3]', 5, 'bbpYuM3Z'], ['[3/3]', 6, 'estouroth24']]

        for texto_tela, spot, senha in spots_por_tela:
            if texto_tela in self.tela:
                self.senha = senha
                return spot
        return 0

    def _definir_comando_inicial(self):
        self.teclado_util.selecionar_skill_1()
        self.up_util.enviar_comandos_iniciais()

    def _mover_mapa(self):
        self._mover_ate_k1_se_necessario()

        if not safe_util.k1(self.handle):
            return

        self._resetar_coordenadas()
        self._esperar_na_safe_se_necessario()

        if self.arduino.conexao_arduino is None:
            GuardaGemstoneService(self.handle, self.mover_spot_util, self.up_util).guardar_gemstone_no_bau()
            self.subir_k3 = False

        if self._deve_subir_para_k3():
            self._subir_para_k3()
            return

        if self._tentar_andar_para_k2():
            return

        self._mover_mapa()

    def _deve_subir_para_k3(self):
        return self.subir_k3 and self.senha is not None

    def _subir_para_k3(self):
        self._andar_ate_k3()
        self._posicionar_char_spot()

    def _tentar_andar_para_k2(self):
        if self._andar_ate_k2():
            self._posicionar_char_spot()
            return True
        return False

    def _mover_ate_k1_se_necessario(self):
        if safe_util.tk(self.handle) or safe_util.tk2_portal(self.handle):
            if safe_util.tk(self.handle):
                self.mover_spot_util.movimentar_tarkan((157, 58))

            while True:
                limpar_mob_ao_redor_util.limpar_mob_ao_redor(self.handle)
                movimentou = self.mover_spot_util.movimentar_tarkan((8, 199), verficar_se_movimentou=True,
                                                                    limpar_spot_se_necessario=True,
                                                                    max_tempo=240)
                if movimentou:
                    mouse_util.left_clique(self.handle, 281, 207)
                    time.sleep(2)

                if safe_util.k1(self.handle):
                    break

    def _resetar_coordenadas(self):
        self.coord_spot_atual = None
        self.coord_mouse_atual = None

    def _esperar_na_safe_se_necessario(self):
        if not self.iniciou_up:
            self.iniciou_up = True
        else:
            self._registrar_morte()
            self._aplicar_tempo_de_espera()

    def _registrar_morte(self):
        agora = datetime.now()
        self.mortes.append(agora)
        self.mortes = [m for m in self.mortes if agora - m < timedelta(minutes=60)]

    def _aplicar_tempo_de_espera(self):
        if len(self.mortes) >= 3:
            self.subir_k3 = True
            self.mortes = []
            total_wait_time = 10
        else:
            self.subir_k3 = False
            # total_wait_time = random.choice([120, 180, 340, 400, 460])
            total_wait_time = random.choice([120, 180])

        num_intervals = 5

        # Gera pequenas variações nos intervalos, mantendo a média
        base_interval = total_wait_time / num_intervals
        intervals = [random.uniform(base_interval * 0.8, base_interval * 1.2) for _ in range(num_intervals)]

        # Ajusta a soma para bater exatamente com o tempo total
        scale_factor = total_wait_time / sum(intervals)
        intervals = [int(i * scale_factor) for i in intervals]

        waited_time = 0
        for interval in intervals:
            print(f"Aguardando {total_wait_time - waited_time} segundos... " + self.tela)
            time.sleep(interval)
            waited_time += interval

        print("Tempo de espera finalizado. Retornando para o local de farm. " + self.tela)

    def _andar_ate_k3(self):
        movimentacao_k3 = MovimentacaoVotaK3ParaK2Service(self.handle, self.mover_spot_util, self.arduino, self.senha)
        movimentacao_k3.mover_para_k3()
        self.iniciou_up = movimentacao_k3.iniciou_up

    def _andar_ate_k2(self):
        movimentacao_inicial_bot = MovimentacaoInicialBotK1k2Service(self.handle, self.spot_up, self.mover_spot_util)
        return movimentacao_inicial_bot.executar_movimentacao_inicial()

    def _corrigir_coordenada_e_mouse(self):
        if (time.time() - self.tempo_inicial_corrigir_coordenada_e_mouse) > 120:
            self.tempo_inicial_corrigir_coordenada_e_mouse = time.time()
            if self.coord_spot_atual:
                self.mover_spot_util.movimentar_kanturu_1_2(self.coord_spot_atual, verficar_se_movimentou=True)
        if self.coord_mouse_atual:
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def limpar_mob_ao_redor(self):
        self.tempo_inicial_limpar_mob_ao_redor = self.up_util.limpar_mob_ao_redor(
            self.tempo_inicial_limpar_mob_ao_redor,
            self.classe)

    def _ativar_skill(self):
        self.tempo_inicial_ativar_skill = self.up_util.ativar_skill(self.classe, self.tempo_inicial_ativar_skill)

    def _posicionar_char_spot(self):
        spots = spot_util.buscar_spots_k1_k2()
        poscionar = PosicionamentoSpotService(self.handle, self.pointer, self.mover_spot_util, self.classe,
                                              self.spot_up, spots,
                                              PathFinder.MAPA_KANTURU_1_E_2)
        poscionar.posicionar_bot_farm()
        self.chegou_spot = poscionar.get_chegou_ao_spot()
        self.coord_mouse_atual = poscionar.get_coord_mouse()
        if self.chegou_spot:
            self.coord_spot_atual = poscionar.get_coord_spot()
        else:
            self.coord_spot_atual = (self.pointer.get_cood_y(), self.pointer.get_cood_x())

    def _guardar_gem_no_inventario_se_necessario(self):
        if self.arduino.conexao_arduino:
            gem_spot = GemNoSpotUtil(self.handle, self.arduino, self.tempo_inicial_gem)
            if gem_spot.verificar_gem():
                SelecionarCharUtil(self.handle, self.arduino).reiniciar_char()
                GuardaGemstoneService(self.handle, self.mover_spot_util, self.up_util).guardar_gemstone_no_bau()
                self.iniciou_up = False
            self.tempo_inicial_gem = gem_spot.tempo_inicial_gem
