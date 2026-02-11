# fmt: off

from typing import Any

from msgspec import json

from ..kinds import is_class_t, is_function_t, is_module_t, is_coroutine_t, is_iterator_t, is_type_t
from ..attrs import NAME, QUALNAME, MODULE, FILE
from ..resource.handle import get_handle


__all__ = [
    'fmt_json',
    'dec_json',
    'enc_json',
    'pprint_json',
    'get_json_schema',
]


################################################################################

def fmt_json(data: bytes | str, multiline: bool = True) -> str:
    try:
        if type(data) is bytes:
            data = data.decode('utf8')
        return json.format(data, indent=(2 if multiline else 0))
    except:
        return '<corrupt json str/bytes>'


################################################################################

def json_enc_hook(obj: Any) -> Any:

    cls = type(obj)
    type_name = get_str_attr(cls, QUALNAME)

    data: dict[str, Any]

    if issubclass(cls, BaseException):
        data = dict(__kind__='exception', type=type_name, args=obj.args)

    elif is_class_t(obj):
        qualname = get_str_attr(obj, QUALNAME)
        module = get_str_attr(obj, MODULE)
        bases = [get_str_attr(b, QUALNAME) for b in obj.__bases__]
        data = dict(__kind__='class', type=type_name, qualname=qualname, module=module, bases=bases)

    elif is_function_t(obj):
        qualname = get_str_attr(obj, QUALNAME)
        module = get_str_attr(obj, MODULE)
        data = dict(__kind__='function', type=type_name, qualname=qualname, module=module)

    elif is_module_t(obj):
        name = get_str_attr(obj, NAME)
        file = get_str_attr(obj, FILE)
        data = dict(__kind__='module', type=type_name, name=name, file=file)

    elif is_coroutine_t(obj):
        name = get_str_attr(obj, NAME)
        qualname = get_str_attr(obj, QUALNAME)
        data = dict(__kind__='coroutine', type=type_name, name=name, qualname=qualname)

    elif is_iterator_t(obj):
        data = dict(__kind__='iterator', type=type_name)

    elif is_type_t(obj):
        from ...core.type import anno_str
        f_anno = anno_str(obj)
        data = dict(__kind__='type', anno_str=f_anno)

    else:
        data = dict(__kind__='object', type=type_name)

    if handle := get_handle(obj):
        data['virtual'] = dict(kind=handle.kind, grid=handle.grid, fkey=handle.fkey)

    return data


################################################################################

def get_json_schema(obj: Any) -> dict:
    try:
        return json.schema(obj)
    except:
        pass
    try:
        return {'type': 'instance', 'class': json.schema(type(obj))}
    except:
        pass
    return {}


################################################################################

def get_str_attr(obj: Any, attr: str) -> str | None:
    val = getattr(obj, attr, None)
    return val if type(val) is str else None


################################################################################

def pprint_json(msg: bytes, err: bool = False) -> None:
    from ...core.print import pprint
    data = dec_json(msg)
    pprint(data, err=err)


################################################################################

dec_json = json.Decoder().decode
enc_json = json.Encoder(enc_hook=json_enc_hook, order='sorted').encode
