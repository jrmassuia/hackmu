import time

from interface_adapters.up.use_case.up_base import UpBase
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import spot_util, safe_util


class UpAidaUseCaseNovo(UpBase):

    def executar(self):
        if not self.ja_moveu_para_mapa:
            if not self.verficar_se_char_ja_esta_spot():
                self.teclado_util.escrever_texto('/move aida2')
                time.sleep(2)
                self.posicionar_char_spot()
            else:
                self.up_liberado = True

            self.ja_moveu_para_mapa = True

        if self.up_liberado is False or safe_util.aida(self.pointer.get_coordernada_y_x()):
            self.ja_moveu_para_mapa = False
            print('Esperando na safe de aida por 120s')
            time.sleep(120)  # ESPERA PRA VOLTAR PRO SPOT
        else:
            self.auto_pick.execute()
            self.limpar_mob_ao_redor()
            self.ativar_skill()
            self.corrigir_coordenada_e_mouse()

        return self.up_liberado

    def posicionar_char_spot(self, iniciar_por_aida_2=True):

        if iniciar_por_aida_2:
            spots_aida2 = []
            spots_aida2.extend(spot_util.buscar_spots_aida_2())
            spots_aida2.extend(spot_util.buscar_spots_aida_corredor())
            spots_aida2.extend(spot_util.buscar_spots_aida_final())
            spots_aida2.extend(spot_util.buscar_spots_aida_volta_final())
            spots = spots_aida2
        else:
            spots = spot_util.buscar_spots_aida_1()

        poscionar = PosicionamentoSpotService(spots)

        achou_spot = poscionar.posicionar_bot_up()

        if not iniciar_por_aida_2 and not achou_spot:
            # Se não achou em Aida 1, espera e tenta subir pra Aida 2
            print('ESPERANDO 300s para voltar a procura spot aida!')
            time.sleep(300)
            self.mover_spot_util.movimentar(
                (207, 169),
                max_tempo=3600,
                movimentacao_proxima=True
            )
            self.posicionar_char_spot()  # Volta a procurar em Aida 2
            return  # Impede de continuar com os dados antigos

        if not achou_spot:
            # Se não achou em Aida 2, tenta Aida 1
            self.teclado_util.escrever_texto('/move aida')
            time.sleep(2)
            self.sair_da_safe()
            self.posicionar_char_spot(iniciar_por_aida_2=False)
            return  # Impede de continuar com os dados antigos

        # Se encontrou o spot, atualiza as coordenadas
        if achou_spot:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()
            self.up_liberado = True
        else:
            self.up_liberado = False

    def sair_da_safe(self):
        self.mover_spot_util.movimentar((100, 10), movimentacao_proxima=True)
