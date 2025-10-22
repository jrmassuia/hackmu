import time
from typing import Sequence, Callable, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import mouse_util, safe_util, spot_util, limpar_mob_ao_redor_util
from utils.rota_util import PathFinder


class PkKanturuUseCase(PkBase):
    """
    PK para Kanturu (K1 / K2).
    Mantive a lógica de definição de senha por nome, movimentações entre mapas e método iniciar_pk.
    """

    PKLIZAR_K1 = 'KANTURU_1'
    PKLIZAR_K2 = 'KANTURU_2'

    def _definir_tipo_pk_e_senha(self) -> str:
        nome = self.pointer.get_nome_char()
        senha = ''

        if nome == 'Heisemberg':
            senha = '93148273'
            self.tipo_pk = self.PKLIZAR_K2
        elif nome == 'SM_Troyer':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_K2
        else:
            self.tipo_pk = self.PKLIZAR_K1

        return senha

    def iniciar_pk(self):
        # garantir mapa KANTURU (o fluxo original reseta mapa para TK em alguns casos)
        self.mapa = PathFinder.MAPA_KANTURU_1_E_2
        self.mover_para_sala7()
        self._mover_para_k1()
        self._sair_da_safe()
        self._ativar_skill()

        if self.tipo_pk == self.PKLIZAR_K1:
            self.pklizar_kanturu1()
        elif self.tipo_pk == self.PKLIZAR_K2:
            self.pklizar_kanturu2()

    def _sair_da_safe(self):
        if safe_util.k1(self.handle):
            if self._verificar_se_limpo():
                self.mover_spot.movimentar_kanturu_1_2((46, 222), movimentacao_proxima=True)
            else:
                mouse_util.left_clique(self.handle, 472, 40)  # VOLTA PARA TK PARA LIMPAR PK
                time.sleep(5)
        elif safe_util.tk(self.handle):
            self.mover_spot.movimentar_tarkan((205, 86), movimentacao_proxima=True)

    def pklizar_kanturu1(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k1,
            spot_util.buscar_spots_k2,
        )
        self.executar_rota_pk(etapas)

    def pklizar_kanturu2(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k2,
            spot_util.buscar_spots_k1,
        )
        self.executar_rota_pk(etapas)

    def morreu(self) -> bool:
        return safe_util.k1(self.handle)

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            if self.mapa == PathFinder.MAPA_KANTURU_1_E_2:
                self.mover_spot.movimentar_kanturu_1_2(
                    self.coord_spot_atual,
                    verficar_se_movimentou=True
                )
            elif self.mapa == PathFinder.MAPA_TARKAN:
                self.mover_spot.movimentar_tarkan(
                    self.coord_spot_atual,
                    verficar_se_movimentou=True
                )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot.movimentar_kanturu_1_2(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x, y):
        return self.mover_spot.movimentar_kanturu_1_2(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )

    def _mover_para_k1(self):
        if safe_util.tk(self.handle):
            self.teclado.selecionar_skill_1()
            while True:
                self.mover_spot.movimentar_tarkan((170, 58), movimentacao_proxima=True)

                movimentou = self.mover_spot.movimentar_tarkan(
                    (12, 200),
                    verficar_se_movimentou=True,
                    limpar_spot_se_necessario=True,
                    movimentacao_proxima=True,
                    max_tempo=240
                )

                if movimentou:
                    limpar_mob_ao_redor_util.limpar_mob_ao_redor(self.handle)
                    movimentou = self.mover_spot.movimentar_tarkan((12, 200), verficar_se_movimentou=True,
                                                                   max_tempo=240)

                if movimentou:
                    mouse_util.left_clique(self.handle, 158, 139)

                time.sleep(5)  # aguardar carregamento/teleporte

                if safe_util.k1(self.handle):
                    break

                if safe_util.tk(self.handle):
                    print('Morreu tentando subir para K1 — aguardando 300s')
                    time.sleep(300)

    def _esta_na_safe(self):
        return safe_util.k1(self.handle) or safe_util.tk(self.handle)
