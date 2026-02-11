# fmt: off


from .__ import *
from .base import *


__all__ = [
    'ModuleData',
]


################################################################################

class ModuleData(ResourceData):
    __slots__ = 'name', 'doc', 'file', 'package', 'exports', 'hidden', 'annos',

    KIND = Kind.Module
    FORBIDDEN_FORM = forbidden_module

    name:    str
    doc:     optstr
    file:    optstr
    package: optstr
    exports: Rec[TermT]
    hidden:  strtup
    annos:   AnnotationsT

    def create_resource(self, handle: ResourceHandle) -> ModuleType: ...

################################################################################

def describe_real_module(mod: ModuleT) -> ModuleData:

    name, file, doc, annos, syms = multi_get_raw(mod, NAME, FILE, DOC, ANNOS, ALL)

    assert is_str(name), "name must be a string"
    assert is_optstr(file), "file must be a string or None"
    assert is_optstr(doc), "doc must be a string or None"
    assert is_rec(annos), "annos must be a record"
    assert syms is None or is_strlist(syms), "exports must be a list of strings or None"

    if is_forbidden(mod, name):
        raise E.WarpEncodingForbiddenError(f"<module {name!r}>")

    data = ModuleData()

    data.name = name
    data.file = sanitize_path(file)
    data.doc = doc
    data.annos = annos
    data.package = getattr(mod, '__package__', None)

    if log := bool(LOG_ENCR):
        P.nprint(ICON_CM, f"encoding module '{name}'")

    keys = tuple(mod.__dir__())
    data.exports, add_export = mkdict()
    if syms:
        for key in syms or ():
            if type(key) is not str:
                continue
            if key not in keys:
                continue
            val = getattr(mod, key, FIELD_ABSENT)
            if val is not FIELD_ABSENT:
                if not is_cheap(val):
                    val = ON_DEMAND
                add_export(key, val)

    data.hidden = tuple(
        k
        for k in keys
        if not k.startswith('__') and k not in data.exports
    )

    if log:
        num_exp = len(data.exports)
        num_nod = sum(0 if d is ON_DEMAND else 1 for d in data.exports.values())
        num_hid = len(data.hidden)
        P.nprint(ICON_CM, f"module '{name}' had {num_nod}/{num_exp} exports and {num_hid} hiddens")

    return data

PACKAGE = '__package__'

################################################################################

class module(ModuleType):

    def __init__(self, name: str, doc: str | None, **kwargs) -> None:
        super().__init__(name, doc)
        if ON_DEMAND in kwargs.values():
            kwargs = ((k, v) for k, v in kwargs.items() if v is not ON_DEMAND)
        self.__dict__.update(kwargs)

    def __getattr__(self, name: str) -> Any:
        # P.nprint(ICON_I, f'virtual module attr {name!r}')
        handle = obj_handle(self)
        value = handle.hdlr(handle, ResourceGetAttr(self, name))
        # P.nprint(ICON_I, f'value =', type(value))
        self.__dict__[name] = value
        return value

    def __getattrs__(self, attrs: tuple[str, ...]) -> Any:
        if not attrs: return ()
        handle = obj_handle(self)
        values = handle.hdlr(handle, ResourceGetAttr(self, attrs))
        if type(values) is tuple and len(values) == len(attrs):
            self.__dict__.update(
                (a, v) for a, v in zip(attrs, values)
                if v is not FIELD_ABSENT
            )
        return values

    def __setattr__(self, name: str, value: Any) -> None:
        raise TypeError('this module is immutable')

    def __delattr__(self, name: str):
        raise TypeError('this module is immutable')

    def __dir__(self) -> list[str]:
        return obj_handle(self).keys


module.__module__ = 'virtual'

################################################################################

def create_virtual_module(data: ModuleData, handle: ResourceHandle) -> ModuleType:

    if log := bool(LOG_DECR):
        P.nprint(ICON_C0, f"decoding module '{data.name}'")

    exports = data.exports
    hidden = data.hidden

    export_keys = list(exports.keys())

    handle.kind = Kind.Module
    handle.keys = [*hidden, *export_keys]
    handle.open = False
    handle.name = f'<{data.name!r} module>'

    meta = {
        FILE: data.file,
        ALL: export_keys,
        ANNOS: data.annos,
        VHDL: handle,
        PACKAGE: data.package,
        **exports
    }

    v_mod = module(data.name, data.doc, **meta)

    if log:
        P.nprint(ICON_C1, f"created module '{data.name}'")

    return v_mod

################################################################################

ModuleData.describe_resource = staticmethod(describe_real_module)
ModuleData.create_resource = create_virtual_module
