# fmt: off

from .__ import *
from .base import Msg

__all__ = [
    'RPCMsg',
]


################################################################################

if TYPE_CHECKING:
    from .term_result import ResultMsg
    from .term import TermMsg
    from .resource_def import DefinitionMsg
    from .msg_aliases import SrcLocationMsg

################################################################################

class RPCMsg(Msg):
    """ABC for RPC messages, whether requests or replies."""

    if TYPE_CHECKING:
        origin: SrcLocationMsg

    ################################################################################

    def get_result_msg(self) -> 'ResultMsg | None':
        return None

    def get_term_msg(self) -> 'TermMsg | None':
        if msg := self.get_result_msg():
            return msg.value
        return None

    def get_error_msg(self) -> 'TermMsg | None':
        if msg := self.get_result_msg():
            return msg.error
        return None

    def get_definition_msgs(self) -> 'Tup[DefinitionMsg] | None':
        return None
