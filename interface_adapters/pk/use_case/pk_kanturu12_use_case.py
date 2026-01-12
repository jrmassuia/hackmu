import time
from typing import Sequence, Callable, List

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import safe_util, spot_util, mouse_util


class PkKanturu12UseCase(PkBase):

    def execute(self):
        while True:
            self.iniciar_pk()

    def iniciar_pk(self):
        nome = self.pointer.get_nome_char()

        self._esperar_safe_se_necessario()
        self.atualizar_lista_player()
        self._sair_da_safe()
        self._ativar_skill()

        if nome == 'ReiDav1':
            self._pklizar_bot_kanturu()
        else:
            self._pklizar_kanturu()

        self.voltar_pra_safe_e_esperar_proximo_pk()

    def _pklizar_kanturu(self):
        etapas: Sequence[Callable[[], List]] = (
            spot_util.buscar_spots_k2,
            spot_util.buscar_spots_k1
        )
        self.executar_rota_pk(etapas)

    def _pklizar_bot_kanturu(self):
        etapas: Sequence[Callable[[], List]] = (
            self.spot_bot,
        )
        self.executar_rota_pk(etapas)

    def spot_bot(self):
        coordenadas = []
        coordenadas.extend([
            [
                [['SM'], [(153, 236)], (0, 0)]
            ],
            [
                [['SM'], [(168, 225)], (0, 0)]
            ],
            [
                [['SM'], [(178, 202)], (0, 0)]
            ]
        ])
        return coordenadas

    def _esperar_safe_se_necessario(self):
        if self.morreu:
            print('Morreu no Kanturu. Aguardando na safe…')
            self.morreu = False
            if self.pointer.get_nome_char() == 'ReiDav1':
                time.sleep(60)
            else:
                time.sleep(300)

    def _sair_da_safe(self):
        if safe_util.k1(self.handle):
            self.mover_spot.movimentar((41, 231), movimentacao_proxima=True)

    def voltar_pra_safe_e_esperar_proximo_pk(self):
        if not self.morreu:
            nome = self.pointer.get_nome_char()
            if nome == 'ReiDav1':
                movimentou = self.mover_spot.movimentar(
                    (154, 236),
                    verficar_se_movimentou=True
                )
                if movimentou:
                    mouse_util.desativar_click_direito(self.handle)
                    self.pklizar.ativar_pk()
                    mouse_util.mover(self.handle, 286, 164)
                    time.sleep(0.5)
                    mouse_util.ativar_click_direito(self.handle)
                    print('ESPERANDO 60s PARA PROXIMO PK EM KANTURU ' + nome)
                    time.sleep(60)
                    mouse_util.desativar_click_direito(self.handle)

            else:
                self.mover_spot.movimentar(
                    (35, 211),
                    verficar_se_movimentou=True,
                    movimentacao_proxima=True,
                    max_tempo=360
                )
                if self.mover_spot.esta_na_safe:
                    print('ESPERANDO 120s PARA PROXIMO PK EM KANTURU ' + nome)
                    time.sleep(120)
        else:
            time.sleep(8)  # DELAY PARA CASO MORRA E VOLTAR PARA SAFE

    def morreu(self) -> bool:
        return safe_util.k1(self.handle)

    def _esta_na_safe(self):
        return safe_util.k1(self.handle) or safe_util.tk(self.handle)

    def _definir_tipo_pk_e_senha(self) -> str:
        return ''

    def verificar_se_pode_continuar_com_pk(self) -> bool:
        return True
