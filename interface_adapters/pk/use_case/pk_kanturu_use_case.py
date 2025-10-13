from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import mouse_util, safe_util, spot_util


class PkAidaUseCase(PkBase):
    PKLIZAR_k1 = 'KANTURU_1'
    PKLIZAR_k2 = 'KANTURU_2'

    def _definir_tipo_pk_e_senha(self) -> str:
        nome = self.pointer.get_nome_char()
        senha = ''

        if nome == 'AlfaVictor':
            senha = 'thiago123'
            self.tipo_pk = self.PKLIZAR_k1
        elif nome == 'ReiDav1':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_k2

        return senha

    def iniciar_pk(self):
        self.mover_para_sala7()
        self.teclado_util.escrever_texto('/re off')
        self._sair_da_safe()
        self._ativar_skill()

        if self.tipo_pk == self.PKLIZAR_k1:
            self.pklizar_kanturu1()
        elif self.tipo_pk == self.PKLIZAR_k2:
            self.pklizar_kanturu2()

    def _sair_da_safe(self):
        if safe_util.k1(self.handle):
            self.mover_spot_util.movimentar_kanturu_1_2((46, 222), movimentacao_proxima=True)

    def pklizar_kanturu1(self):
        etapas = (
            spot_util.buscar_spots_k1()
        )
        self.executar_rota_pk(etapas)

    def pklizar_kanturu2(self):
        etapas = (
            spot_util.buscar_spots_k2,
        )
        self.executar_rota_pk(etapas)

    def pklizar_no_dinasty(self):
        etapas = (
            spot_util.buscar_spots_k1_k2(),
        )
        self.executar_rota_pk(etapas)

    def morreu(self) -> bool:
        return safe_util.k1(self.handle)

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar_kanturu_1_2(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot_util.movimentar_kanturu_1_2(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x, y):
        return self.mover_spot_util.movimentar_kanturu_1_2(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )
