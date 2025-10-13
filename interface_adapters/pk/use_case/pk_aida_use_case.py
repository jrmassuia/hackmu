import time

from interface_adapters.pk.use_case.pk_base_use_case import PkBase
from utils import spot_util, safe_util, mouse_util


class PkAidaUseCase(PkBase):
    PKLIZAR_AIDA_1 = 'AIDA_1'
    PKLIZAR_AIDA_2 = 'AIDA_2'
    PKLIZAR_AIDA_CORREDOR = 'AIDA_CORREDOR'
    PKLIZAR_AIDA_FINAL = 'AIDA_FINAL'

    # ---------- Definição de senha/tipo ----------
    def _definir_tipo_pk_e_senha(self) -> str:
        nome = self.pointer.get_nome_char()
        senha = ''

        # AIDA 1
        if nome == 'AlfaVictor':
            senha = 'thiago123'
            self.tipo_pk = self.PKLIZAR_AIDA_1
        elif nome == 'ReiDav1':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_AIDA_1

        # AIDA 2
        elif nome == 'LAZLU':
            senha = 'bebe133171'
            self.tipo_pk = self.PKLIZAR_AIDA_2
        elif nome == 'DL_JirayA':
            senha = '134779'
            self.tipo_pk = self.PKLIZAR_AIDA_2
        elif nome == 'Omale_DL':
            senha = 'gtkn6iVy'
            self.tipo_pk = self.PKLIZAR_AIDA_2

        # AIDA CORREDOR
        elif nome == 'SM_Troyer':
            senha = 'romualdo12'
            self.tipo_pk = self.PKLIZAR_AIDA_CORREDOR
        elif nome == 'SisteMatyc':
            senha = 'carenae811'
            self.tipo_pk = self.PKLIZAR_AIDA_CORREDOR

        # AIDA FINAL
        elif nome == '_Offensive':
            senha = 'kuChx98f'
            self.tipo_pk = self.PKLIZAR_AIDA_FINAL
        elif nome == 'INFECTRIX':
            senha = '9876Sonso'
            self.tipo_pk = self.PKLIZAR_AIDA_FINAL

        return senha

    # ---------- Entrada do fluxo ----------
    def iniciar_pk(self):
        self.mover_para_sala7()
        self.teclado_util.escrever_texto('/re off')
        self._sair_da_safe()
        self._ativar_skill()

        if self.tipo_pk == self.PKLIZAR_AIDA_1:
            self.pklizar_aida1()
        elif self.tipo_pk == self.PKLIZAR_AIDA_2:
            self.pklizar_aida2()
        elif self.tipo_pk == self.PKLIZAR_AIDA_CORREDOR:
            self.pklizar_aida_corredor()
        elif self.tipo_pk == self.PKLIZAR_AIDA_FINAL:
            self.pklizar_aida_final()
        else:
            # fallback mantido como no original
            self.pklizar_aida1()

    # ---------- Sequências específicas ----------
    def pklizar_aida1(self):
        etapas = (
            lambda: spot_util.buscar_spots_aida_1(ignorar_spot_pk=True),
            self.buscar_spot_extra_aida1,
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_aida2,
        )
        self.executar_rota_pk(etapas)

    def pklizar_aida2(self):
        etapas = (
            self.buscar_spot_aida2,
            spot_util.buscar_spots_aida_corredor,
            spot_util.buscar_spots_aida_final,
            self.buscar_spot_extra_aida1,
        )
        self.executar_rota_pk(etapas)

    def pklizar_aida_corredor(self):
        etapas = (
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_extra_aida1,
            lambda: spot_util.buscar_spots_aida_1(ignorar_spot_pk=True),
            self.buscar_spot_aida2,
            spot_util.buscar_spots_aida_final,
        )
        self.executar_rota_pk(etapas)

    def pklizar_aida_final(self):
        etapas = (
            spot_util.buscar_spots_aida_final,
            spot_util.buscar_spots_aida_corredor,
            self.buscar_spot_extra_aida1,
            self.buscar_spot_aida2,
        )
        self.executar_rota_pk(etapas)

    def buscar_spot_extra_aida1(self):
        spots = spot_util.buscar_spots_aida_1()
        start = max(0, len(spots) - 3)
        spots_extras = []
        for indice_spot in range(start, len(spots)):
            spots_extras.append(spots[indice_spot])
        return spots_extras

    def buscar_spot_aida2(self):
        spots = spot_util.buscar_spots_aida_volta_final(ignorar_spot_pk=True)
        spots.extend(spot_util.buscar_spots_aida_2(ignorar_spot_pk=True))
        return spots

    def _sair_da_safe(self):
        if safe_util.aida(self.handle):
            self._desbugar_goblin()
            self.mover_spot_util.movimentar_aida((140, 14), max_tempo=30, movimentacao_proxima=True)

    def _desbugar_goblin(self):
        btn_fechar = self.buscar_imagem.buscar_item_simples('./static/img/fechar_painel.png')
        if btn_fechar:
            x, y = btn_fechar
            mouse_util.left_clique(self.handle, x, y)
            time.sleep(1)
            mouse_util.left_clique(self.handle, 38, 369)

    def morreu(self) -> bool:
        return safe_util.aida(self.handle)

    def _corrigir_coordenada_e_mouse(self):
        if self.coord_spot_atual and self.coord_mouse_atual:
            self.mover_spot_util.movimentar_aida(
                self.coord_spot_atual,
                verficar_se_movimentou=True
            )
            mouse_util.mover(self.handle, *self.coord_mouse_atual)

    def _movimentar_char_spot(self, coordenadas):
        return self.mover_spot_util.movimentar_aida(
            coordenadas,
            max_tempo=600,
            verficar_se_movimentou=True,
            movimentacao_proxima=True,
            limpar_spot_se_necessario=True
        )

    def _posicionar_char_pklizar(self, x, y):
        return self.mover_spot_util.movimentar_aida(
            (y, x),
            verficar_se_movimentou=True,
            posicionar_mouse_coordenada=True,
            limpar_spot_se_necessario=True
        )
