import sys
import time
from datetime import datetime, time as time_module


class PegarItemComEspacoService:

    def __init__(self, handle, pointer, tempo_inicial_pick):
        self.handle = handle
        self.pointer = pointer
        self.tempo_inicial_pick = tempo_inicial_pick

    def pegar_item_com_espaco(self):
        exe = getattr(sys, 'frozen', False)
        hora_atual = datetime.now().time()
        inicio = time_module(23, 0)
        fim = time_module(7, 30)

        # Verifica se está no horário permitido para pegar item
        if exe or (not exe and (hora_atual >= inicio or hora_atual <= fim)):
            if (time.time() - self.tempo_inicial_pick) > 30:
                while True:
                    self.tempo_inicial_pick = time.time()
                    # self.teclado_util.pressionar_espaco_foco(self.handle)
                    item_pick = self.pointer.get_item_pick()

                    # Condição para parar o loop se não encontrou item desejado
                    if item_pick is None or all(keyword not in item_pick for keyword in
                                                ['Zen', 'Kundun', 'Devil', 'Imp', 'Sing', 'Jewel', 'Complex']):
                        break
