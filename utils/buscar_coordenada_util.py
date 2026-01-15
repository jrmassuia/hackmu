from provider.pointer_provider import get_pointer


def coordernada():
    pointer = get_pointer()
    return pointer.get_cood_y(), pointer.get_cood_x()
