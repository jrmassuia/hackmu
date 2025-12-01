import time
from typing import Sequence, Callable, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import mouse_util, safe_util, spot_util, limpar_mob_ao_redor_util
from utils.rota_util import PathFinder


class PkKanturuUseCase(PkBase):
    PKLIZAR_K1 = 'KANTURU_1'
    PKLIZAR_K2 = 'KANTURU_2'
    PKLIZAR_K1_SETOR_1 = 'KANTURU_1_SETOR_1'

    def _definir_tipo_pk_e_senha(self) -> str:
        nome = self.pointer.get_nome_char()
        senha = ''

        if nome == 'Heisemberg':
            senha = '93148273'
            self.tipo_pk = self.PKLIZAR_K2
        elif nome == 'SM_Troyer':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_K2
        elif nome == 'ESTAMUERTO':
            senha = '93148273'
            self.tipo_pk = self.PKLIZAR_K2
        #
        elif nome == 'INFECTRIX':
            senha = '9876Sonso'
            self.tipo_pk = self.PKLIZAR_K1_SETOR_1
        elif nome == '_Offensive':
            senha = 'kuChx98f'
            self.tipo_pk = self.PKLIZAR_K1_SETOR_1
        elif nome == 'LAZLU':
            senha = 'bebe133171'
            self.tipo_pk = self.PKLIZAR_K1_SETOR_1

        return senha

    def iniciar_pk(self):
        # garantir mapa KANTURU (o fluxo original reseta mapa para TK em alguns casos)
        self.mapa = PathFinder.MAPA_KANTURU_1_E_2
        self.mover_para_sala(self.sala_pk)
        self._mover_portal_tk_para_k1()
        self._sair_da_safe()
        self._ativar_skill()

        if self.tipo_pk == self.PKLIZAR_K1:
            self.pklizar_kanturu1()
        elif self.tipo_pk == self.PKLIZAR_K2:
            self.pklizar_kanturu2()
        elif self.tipo_pk == self.PKLIZAR_K1_SETOR_1:
            self.pklizar_kanturu1_setor1()

    def _sair_da_safe(self):
        if safe_util.k1(self.handle):
            if self.verificar_se_pode_continuar_com_pk():
                self.mover_spot.movimentar((46, 222), movimentacao_proxima=True)
            else:
                mouse_util.left_clique(self.handle, 472, 40)  # VOLTA PARA TK PARA LIMPAR PK
                time.sleep(5)
        elif safe_util.tk(self.handle):
            self.mover_spot.movimentar((205, 86), movimentacao_proxima=True)

    def pklizar_kanturu1(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k1,
            spot_util.buscar_spots_k2,
        )
        return self.executar_rota_pk(etapas)

    def pklizar_kanturu2(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k2,
            spot_util.buscar_spots_k1,
        )
        return self.executar_rota_pk(etapas)

    def pklizar_kanturu1_setor1(self):
        etapas: Sequence[Callable[[], List]] = (
            self.spot_kanturu1_setor1,
        )
        return self.executar_rota_pk(etapas)

    def spot_kanturu1_setor1(self):
        coordenadas = []
        coordenadas.extend([
            [
                [['DL'], [(196, 179)], (321, 183)]  # 6
            ],
            [
                [['DL'], [(219, 158)], (243, 203)]  # 7
            ],
            [
                [['DL'], [(221, 141)], (313, 217)]  # 8
            ],
            [
                [['DL'], [(235, 132)], (230, 362)]  # 9
            ],
            [
                [['DL'], [(235, 96)], (251, 339)]  # 10
            ],
            [
                [['DL'], [(227, 84)], (207, 195)]  # 11
            ],
            [
                [['DL'], [(220, 45)], (204, 269)]  # 12
            ]
        ])
        return coordenadas

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot.movimentar(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot.movimentar(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x, y):
        return self.mover_spot.movimentar(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )

    def _mover_portal_tk_para_k1(self):
        if safe_util.tk(self.handle):
            self.teclado.selecionar_skill_1()
            while True:
                self.mover_spot.movimentar((170, 58), movimentacao_proxima=True)  # SAIR DA SAFE TK

                movimentou = self.mover_spot.movimentar(
                    (12, 200),
                    verficar_se_movimentou=True,
                    limpar_spot_se_necessario=True,
                    movimentacao_proxima=True,
                    max_tempo=240
                )

                if movimentou:
                    limpar_mob_ao_redor_util.limpar_mob_ao_redor(self.handle)
                    movimentou = self.mover_spot.movimentar((12, 200), verficar_se_movimentou=True,
                                                            max_tempo=240)

                if movimentou:
                    mouse_util.left_clique(self.handle, 158, 139)

                time.sleep(5)  # aguardar carregamento/teleporte

                if safe_util.k1(self.handle):
                    break

                if safe_util.tk(self.handle):
                    print('Morreu tentando subir para K1 — aguardando 15s')
                    time.sleep(15)

    def morreu(self) -> bool:
        return safe_util.k1(self.handle)

    def _esta_na_safe(self):
        return safe_util.k1(self.handle) or safe_util.tk(self.handle)
