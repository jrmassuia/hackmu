from abc import ABC, abstractmethod

from sessao_handle import set_handle_atual, limpar_handle_atual
from utils.teclado_util import Teclado_util


class BaseController(ABC):

    def __init__(self, handle: int):
        self.handle = handle
        self._prepared = False

    def execute(self):
        """
        Este método é executado dentro da thread criada pelo MainApp.
        Aqui configuramos o handle da thread e chamamos o "construtor de thread".
        """
        set_handle_atual(self.handle)

        try:
            if not self._prepared:
                Teclado_util().selecionar_skill_1()
                Teclado_util().pressionar_zoon()
                Teclado_util().escrever_texto('/re off')
                #
                self._prepare()  # "construtor de thread"
                self._prepared = True

            self._run()  # lógica principal do controller

        finally:
            limpar_handle_atual()

    @abstractmethod
    def _prepare(self):
        """
        Construtor interno da thread.
        Tudo que depende de get_handle_atual() deve ser instanciado aqui.
        """
        pass

    @abstractmethod
    def _run(self):
        """Lógica principal da thread."""
        pass

    def parar(self):
        """Opcional: pode ser sobrescrito."""
        pass
