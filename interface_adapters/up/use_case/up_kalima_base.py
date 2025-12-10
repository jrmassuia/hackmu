import time

from interface_adapters.up.use_case.up_base import UpBase
from services.posicionamento_spot_service import PosicionamentoSpotService
from utils import mouse_util, acao_menu_util, safe_util, spot_util
from utils.buscar_item_util import BuscarItemUtil


class UpKalimaBase(UpBase):
    KALIMA = 1131413504

    def __init__(self):
        super().__init__()
        self.tentativa_up = 0

    def executar(self):

        if self.classe == 'EF' or (self.ja_moveu_para_mapa is False and self._possui_convite() is False):
            return False

        if not self.ja_moveu_para_mapa:
            # Caso ainda não esteja em Kalima → mover e posicionar
            if self.pointer.get_mapa_atual() != self.KALIMA:
                if not self._mover_e_abrir_portal():
                    return False
                self.posicionar_char_spot()

            # Já está em Kalima → verificar se precisa reposicionar
            elif self.verficar_se_char_ja_esta_spot():
                self.up_liberado = True

            self.ja_moveu_para_mapa = True

        if self.up_liberado:
            if self.pointer.get_mapa_atual() != self.KALIMA:
                if self.tentativa_up > 3:
                    print(f'Atingiou o limite máximo de tentativa up em {self.nome_mapa()}')
                    return False
                else:
                    self.ja_moveu_para_mapa = False
                    self.tentativa_up += 1
                    print(f'Esperando na safe de Devias por 120s para voltar para {self.nome_mapa()}')
                    time.sleep(120)
            else:
                self.auto_pick.execute()
                self.limpar_mob_ao_redor()
                self.ativar_skill()
                self.corrigir_coordenada_e_mouse()
        return self.up_liberado

    def _mover_e_abrir_portal(self):
        self.teclado_util.escrever_texto('/move Devias4')
        time.sleep(2)

        moveu = self.mover_spot_util.movimentar(
            (92, 156),
            limpar_spot_se_necessario=True,
            movimentacao_proxima=True
        )
        if not moveu:
            return False

        acao_menu_util.clicar_inventario(self.handle)
        if not self._esperar_e_jogar_portal():
            return False

        return self._entrar_portal_kalima()

    def _esperar_e_jogar_portal(self):
        tempo_max = 10
        intervalo = 0.25
        tempo_esperado = 0

        while tempo_esperado < tempo_max:
            img_convite = BuscarItemUtil().buscar_item_simples(self.caminho_convite())

            if img_convite:
                cpX, cpY = img_convite
                self.up_util.limpar_mob_ao_redor(None, self.classe)
                mouse_util.left_clique(self.handle, cpX, cpY)
                mouse_util.left_clique(self.handle, 283, 360)
                time.sleep(2)
                return True

            time.sleep(intervalo)
            tempo_esperado += intervalo

        return False

    def _possui_convite(self) -> bool:
        acao_menu_util.clicar_inventario(self.handle)

        tentativa_max = 20
        tentativa = 0

        img_convite = None
        while tentativa < tentativa_max:
            img_convite = BuscarItemUtil().buscar_item_simples(self.caminho_convite())
            if img_convite is not None:
                break
            tentativa += 1

        acao_menu_util.clicar_inventario(self.handle)
        return img_convite is not None

    def _entrar_portal_kalima(self):
        tempo_max = 10
        intervalo = 0.2
        tempo_esperado = 0
        fechou_inventario = False

        while tempo_esperado < tempo_max:
            if safe_util.kalima(self.handle):
                return True

            mouse_util.mover(self.handle, 1, 1)
            img_portal = BuscarItemUtil().buscar_item_simples('./static/img/portalkalima.png')

            if img_portal:
                cpX, cpY = img_portal
                mouse_util.left_clique(self.handle, cpX - 50, cpY + 80)
                time.sleep(3)
            else:
                time.sleep(intervalo)
                tempo_esperado += intervalo
                if not fechou_inventario:
                    acao_menu_util.clicar_inventario(self.handle)
                    fechou_inventario = True

        return False

    def posicionar_char_spot(self):
        self.mover_spot_util.movimentar((102, 20), movimentacao_proxima=True)

        spots = spot_util.buscar_spots_kalima()
        poscionar = PosicionamentoSpotService(spots)

        achou_spot = poscionar.posicionar_bot_up()
        if achou_spot:
            self.coord_mouse_atual = poscionar.get_coord_mouse()
            self.coord_spot_atual = poscionar.get_coord_spot()
            self.up_liberado = True
        else:
            self.up_liberado = False

    # MÉTODOS ABSTRATOS A SEREM IMPLEMENTADOS NAS SUBCLASSES
    def caminho_convite(self):
        raise NotImplementedError()

    def nome_mapa(self):
        raise NotImplementedError()
