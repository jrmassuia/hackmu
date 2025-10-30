from interface_adapters.recrutar.use_case.recrutar_use_case import RecrutarUseCase


class RecrutarController:

    def __init__(self, handle, arduino):
        self.handle = handle
        self.arduino = arduino

    def execute(self):
        RecrutarUseCase(self.handle, self.arduino).execute()
