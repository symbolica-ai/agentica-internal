from dataclasses import dataclass
from typing import Any

import msgspec

from agentica_internal.core.json import JsonObject
from agentica_internal.warpc.kinds import (
    AnnotationsT,
    ClassT,
    FunctionT,
    ModuleT,
    ObjectT,
    TypeT,
    is_class_t,
    is_function_t,
    is_module_t,
    is_type_t,
)

type A = list[B]
type B = int | list[A]

json_schema = msgspec.json.schema


def ext_schema(obj: Any, root: bool = True) -> JsonObject:
    if is_type_t(obj):
        return annotation_schema(obj, root)
    if is_class_t(obj):
        return class_schema(obj, root)
    if is_function_t(obj):
        return function_schema(obj)
    elif is_module_t(obj):
        return module_schema(obj)
    else:
        return object_schema(obj)


def _schema_dict(kind: str, obj: object, **kwargs) -> JsonObject:
    return dict(type=kind, id=id(obj), **kwargs)


def function_schema(obj: FunctionT) -> JsonObject:
    annos, defs = json_schema_annos(getattr(obj, '__annotations__', {}))
    return _schema_dict('function', obj, annotations=annos, defs=defs)


def annotation_schema(anno: TypeT, root: bool = True) -> JsonObject:
    return _schema_dict('annotation', anno)
    # args = obj.__args__
    # name = f'{t_}Callable' if cls is TCallable else f'{a_}Callable'
    # if not args:
    #     return name
    # *dom, cod = args
    # if len(dom) == 1 and type(dom[0]) is EllipT:
    #     dom = dom[0]
    # pair = rec(dom), rec(cod)
    # return gen(name, pair)


def module_schema(mod: ModuleT) -> JsonObject:
    return _schema_dict('module', mod)


def object_schema(obj: ObjectT) -> JsonObject:
    cls = type(obj)
    cls_schema = class_schema(cls)
    cls_name = cls_schema['class_name']
    return _schema_dict('object', obj, class_name=cls_name, class_schema=cls_schema)


def class_schema(cls: ClassT, root: bool = True) -> JsonObject:
    schema = json_schema(foo)
    return _schema_dict(
        'class', cls, class_name=f'{cls.__module__}.{cls.__name__}', class_schema=schema
    )


def json_schema(obj) -> JsonObject:
    # check if msgspec WILL fail, if so dispatch to ext_schema with root = False
    ...
    try:
        return _json_schema(obj, schema_hook=json_schema_hook)
    except:
        return {'type': 'unrepresentable'}


def json_schema_annos(annos: AnnotationsT) -> tuple[JsonObject, JsonObject]:
    if not annos:
        return {}, {}
    try:
        schemas, defs = _json_schema_comps(annos.values(), schema_hook=json_schema_hook)
    except:
        defs = {}
        schemas = []
        for val in annos.values():
            val_schema, val_defs = _json_schema_comps((val,), schema_hook=json_schema_hook)
            defs.update(val_defs)
            schemas.append(val_schema)
    return dict(zip(annos.keys(), schemas)), defs


def class_name(cls: type) -> str:
    return f'{cls.__module__}.{cls.__name__}'


def json_schema_hook(obj: Any) -> dict:
    return {}


_json_schema = msgspec.json.schema
_json_schema_comps = msgspec.json.schema_components


@dataclass
class Clala:
    pass


def foo(i: int) -> Clala: ...


print(ext_schema(foo))
