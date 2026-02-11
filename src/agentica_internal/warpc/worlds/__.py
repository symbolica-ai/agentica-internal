# ruff: noqa
# fmt: off

from pathlib import Path

from ...core.futures import HookableFuture, new_hookable_future

from ..__ import *
from ..alias import *
from ..frame import *
from ..ids import *
from ..msg.all import *
from ..repl import *
from ..attrs import FUTURE_ID
from ..resource.all import *
from ..resource.logging import LOG_VIRT
from ..request.all import *
from ..events import *
from ..data.identifier import get_stack_identifier

from .interface import *

LOG_SEND = LogFlag('_+SEND')
LOG_RECV = LogFlag('_+RECV')

ICON_RECV = P.MEDIUM.K('⟨⟨⟨ RECV')
ICON_SEND = P.MEDIUM.K('⟩⟩⟩ SEND')
ICON_PAIR = P.MEDIUM.K('⟩ ⟨ PAIR')

BIN_MSG_SEP: bytes = b'\0\0BINMSGSEP\0\0'

def load_msg_log(file: Path | str) -> list[RPCMsg]:
    if isinstance(file, str):
        file = Path(file)
    assert file.exists()
    data = file.read_bytes()
    chunks = data.split(BIN_MSG_SEP)
    msgs = []
    for chunk in chunks:
        if chunk:
            msg = RPCMsg.from_msgpack(chunk)
            msgs.append(msg)
    return msgs

def print_msg_log(file: Path | str) -> None:
    if isinstance(file, str):
        file = Path(file)
    P.hdiv()
    print(P.BLUE("MESSAGE LOG"), P.MAGENTA(file.as_posix()))
    msgs = load_msg_log(file)
    for i, msg in enumerate(msgs):
        print()
        print(P.BLUE(f"MESSAGE #{i}"))
        msg.pprint()
    print()
    P.hdiv()
