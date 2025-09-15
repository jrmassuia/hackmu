from utils.pointer_util import Pointers

def coordernada(handle):
    pointer = Pointers(handle)
    return pointer.get_cood_y(), pointer.get_cood_x()