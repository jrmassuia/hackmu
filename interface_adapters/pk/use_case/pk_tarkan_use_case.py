import time

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import safe_util, spot_util, mouse_util


class PktarkanUseCase(PkBase):

    def execute(self):
        while True:
            self.iniciar_pk()

    def _definir_tipo_pk_e_senha(self) -> str:
        return ''

    def iniciar_pk(self):
        # self.mover_para_sala7()
        self.teclado_util.escrever_texto('/re off')
        self._sair_da_safe()
        self._ativar_skill()
        self.pklizar_tarkan()

    def _sair_da_safe(self):
        if safe_util.tk(self.handle):
            self.mover_spot_util.movimentar_tarkan((205, 100), movimentacao_proxima=True)

    def pklizar_tarkan(self):
        etapas = (
            lambda: spot_util.buscar_spots_tk1(),
            lambda: spot_util.buscar_spots_tk2(nao_ignorar_spot_pk=True),
        )
        self.executar_rota_pk(etapas)

    def _pk_pode_continuar(self):
        if self.morreu():
            print('Morreu tk esperando na safe!')
            time.sleep(120)
        return True

    def morreu(self) -> bool:
        return safe_util.tk(self.handle)

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
