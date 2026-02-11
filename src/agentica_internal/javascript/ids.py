# fmt: off

from enum import IntEnum


__all__ = [
    'SysAtomIDs',
    'SysObjectIDs'
]


################################################################################

# this mirrors core.cpython.ids

# in javascript: not objects, but special atomic values
class SysAtomIDs(IntEnum):
    object                  = -1
    string                  = -2
    number                  = -3
    boolean                 = -4
    void                    = -10
    undefined               = -10
    null                    = -10

# ordinary objects
class SysObjectIDs(IntEnum):

    # Classes
    Object                 = -1
    String                 = -2
    Number                 = -3
    Boolean                = -4
    Array                  = -5
    Map                    = -6
    Set                    = -7
    Function               = -8
    Promise                = -9
    None_                  = -10
    Struct                 = -12
    Tuple                  = -13
    Never                  = -14
    Literal                = -15

    # Exceptions
    Error                  = -50
    AttributeError         = -51
    KeyError               = -52
    ValueError             = -53
    TypeError              = -54

    # Objects
    console                = -101
    Math                   = -102
    JSON                   = -103

    # Functions
    parseInt               = -201
    parseFloat             = -202
    isNaN                  = -203
    isFinite               = -204
    magicRepr              = -301
    console_log            = -302
    magicStackTrace        = -303
    magicLen               = -304
    magicKeys              = -305
    magicStr               = -306

    magicInstanceof        = -310  # NOT IMPLEMENTED
    Object_entries         = -401
    Object_keys            = -402
    Object_is              = -403
    Reflect_getPrototypeOf = -501
    Reflect_isExtensible   = -502
    Reflect_has            = -503
    Reflect_get            = -504  # NOT IMPLEMENTED


# in 3.13 we could use ._add_alias_ instead
def add_aliases(members: dict):
    aliases = {
        k.strip('_').replace('_', '.'): v
        for k, v in members.items()
        if '_' in k
    }
    members.update(aliases)

add_aliases(SysObjectIDs._member_map_)
del add_aliases
