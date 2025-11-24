from interface_adapters.up.up_util.up_util import Up_util


class MovimentacaoInicialBotK1k2Service:
    def __init__(self, handle, spot_up, mover_spot_util, conexao_arduino=None):
        self.handle = handle
        self.mover_spot_util = mover_spot_util
        self.spot_up = spot_up
        self.subir_lateral = False
        self.up_util = Up_util()

    def executar_movimentacao_inicial(self):
        self.mover_spot_util.movimentar(
            (46, 222),
            movimentacao_proxima=True
        )  # SAIR DA SAFE

        # movimentou = True

        # 3. Movimentação lateral em escada (se necessário)
        # if self.spot_up > 3 and self.subir_lateral:
        #     movimentou = self._subir_escada_lateral()

        # 4. Movimento final com base no spot atual
        movimentou = self._mover_para_destino_final()

        # 5. Finaliza modo de up
        self.up_util.desativar_up()

        # 6. Lida com falha
        if not movimentou:
            print("Falha ao se mover. Interrompendo trajeto.")
            return False

        return True

    def _subir_escada_lateral(self):
        coordenadas = [
            (56, 233),
            (65, 236),
            (71, 238),
            (78, 241),
            (139, 241),
            (176, 222),
        ]
        for coord in coordenadas:
            movimentou = self.mover_spot_util.movimentar(
                coord,
                verficar_se_movimentou=True,
                movimentacao_proxima=True
            )
            if not movimentou:
                return False
        return True

    def _mover_para_destino_final(self, movimentou=True):
        if not movimentou:
            return False

        if self.spot_up > 11:
            destino = (205, 38)
            tempo = 999999
        elif self.spot_up < 3:
            destino = (50, 233)
            tempo = 30
        else:
            return movimentou  # Nenhum destino extra

        return self.mover_spot_util.movimentar(
            destino,
            max_tempo=tempo,
            limpar_spot_se_necessario=True,
            verficar_se_movimentou=True,
            movimentacao_proxima=True
        )
