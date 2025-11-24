import threading

_ctx = threading.local()


def set_handle_atual(handle: int) -> None:
    _ctx.handle = handle


def get_handle_atual(default=None) -> int | None:
    return getattr(_ctx, "handle", default)


def limpar_handle_atual() -> None:
    if hasattr(_ctx, "handle"):
        del _ctx.handle
