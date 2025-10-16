import time

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import safe_util, spot_util, mouse_util, limpar_mob_ao_redor_util


class PktarkanUseCase(PkBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pklizou = False

    def execute(self, loop=True):

        def ciclo():
            self.pklizou = False
            # self.iniciar_pk()
            self._mover_para_k1()

        if not loop:
            ciclo()
            return

        while True:
            ciclo()

    def iniciar_pk(self):
        self.esperar_safe_se_necessario()
        self._sair_da_safe()
        self._ativar_skill()
        self.pklizar_tarkan()

    def _sair_da_safe(self):
        if safe_util.tk(self.handle):
            saiu_safe = self.mover_spot_util.movimentar_tarkan((205, 100), movimentacao_proxima=True)
            if not saiu_safe:
                self.morreu = True

    def pklizar_tarkan(self):
        etapas = (
            lambda: spot_util.buscar_spots_tk1(),
            lambda: spot_util.buscar_spots_tk2(nao_ignorar_spot_pk=True),
        )
        self.executar_rota_pk(etapas)

    def esperar_safe_se_necessario(self):
        if self.morreu:
            print('Morreu tk esperando na safe!')
            self.morreu = False
            time.sleep(300)

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar_tarkan(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot_util.movimentar_tarkan(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x, y):
        return self.mover_spot_util.movimentar_tarkan(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )

    def _mover_para_k1(self):
        if safe_util.tk(self.handle):
            return

        while True:
            movimentou = self.mover_spot_util.movimentar_tarkan((12, 201), verficar_se_movimentou=True,
                                                                limpar_spot_se_necessario=True,
                                                                movimentacao_proxima=True,
                                                                max_tempo=240)

            if movimentou:
                if safe_util.k1(self.handle):
                    self.pklizou = True
                    break

                limpar_mob_ao_redor_util.limpar_mob_ao_redor(self.handle)
                movimentou = self.mover_spot_util.movimentar_tarkan((8, 199), verficar_se_movimentou=True,
                                                                    max_tempo=240)
            if movimentou:
                mouse_util.left_clique(self.handle, 281, 207)
                time.sleep(3)

            if safe_util.k1(self.handle):
                self.pklizou = True
                break

    def morreu(self) -> bool:
        return self.morreu

    def pk_pode_continuar(self):
        return True

    def _definir_tipo_pk_e_senha(self) -> str:
        return ''
