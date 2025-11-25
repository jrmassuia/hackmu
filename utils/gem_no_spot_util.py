import time

from interface_adapters.up.up_util.up_util import Up_util
from utils.buscar_item_util import BuscarItemUtil


class GemNoSpotUtil:

    def __init__(self, handle, conexao_arduino, tempo_inicial_gem):
        self.handle = handle
        self.tempo_inicial_gem = tempo_inicial_gem
        self.up_util = Up_util()

    def verificar_gem(self):
        if (time.time() - self.tempo_inicial_gem) > 120:
            self.tempo_inicial_gem = time.time()
            self.up_util.acao_painel_personagem("v")  # ABRIR
            achou = BuscarItemUtil().buscar_item_simples('./static/inventario/gemstone.png')
            self.up_util.acao_painel_personagem("v", abrir=False)  # FECHAR
            return achou is not None
        return False
