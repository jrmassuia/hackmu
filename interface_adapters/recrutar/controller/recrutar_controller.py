from interface_adapters.controller.BaseController import BaseController
from interface_adapters.recrutar.use_case.recrutar_use_case import RecrutarUseCase
from sessao_handle import get_handle_atual


class RecrutarController(BaseController):

    def _prepare(self):
        self.handle = get_handle_atual()

    def _run(self):
        RecrutarUseCase(self.handle).execute()
