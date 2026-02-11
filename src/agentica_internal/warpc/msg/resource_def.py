# fmt: off

from .__ import *
from .base import Msg


__all__ = [
    'DefinitionMsg',
]


################################################################################

if TYPE_CHECKING:
    from .resource_data import ResourceDataMsg
    from .term_resource import UserResourceMsg

################################################################################

class DefinitionMsg(Msg, tag='def'):
    """ABC for messages describing or referencing previously described resource terms."""

    rid: GlobalRID
    data: 'ResourceDataMsg'

    @property
    def as_ref(self) -> 'UserResourceMsg':
        from .term_resource import UserResourceMsg
        return UserResourceMsg(self.rid)

    def __debug_info_str__(self) -> str:
        return f'rid={f_grid(self.rid)}, data={self.data.shape}'

    def __shape__(self) -> str:
        return f_grid(self.rid) + ', ' + self.data.shape

    def repr(self, deep: bool = True) -> str:
        f_data = self.data.repr(False)
        return f'DefinitionMsg({f_grid(self.rid)}, {f_data})'

    def __rich_repr__(self):
        yield f_grid(self.rid)
        yield self.data

    ############################################################################

    def __trans_def_kind__(self) -> Kind:
        return self.data.KIND

    def __trans_int_uid__(self) -> int:
        raise self.rid[2]
