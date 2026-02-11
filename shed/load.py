import typing as T
from importlib import import_module
from linecache import getline
from pathlib import Path
from sys import modules as sys_modules
from types import FunctionType, ModuleType

__all__ = [
    'get_shed_module',
    'get_shed_function',
    'get_shed_class',
    'get_shed_method',
]


THIS_DIR = Path(__file__).parent


NOT_THERE = object()

_original_overload = T.overload


# this is like overload, but doesn't return _overload_dummy, since this ruins typeshed import
def _patched_overload(func: T.Callable) -> T.Callable:
    f = getattr(func, "__func__", func)
    try:
        T._overload_registry[f.__module__][f.__qualname__][f.__code__.co_firstlineno] = func  # type: ignore
    except AttributeError:
        # Not a normal function; ignore.
        pass
    return func


def process_module(module: ModuleType, prefix: str = '') -> ModuleType:
    assert hasattr(module, '__all__')

    _names = list(module.__all__)
    if prefix:
        _names = [n for n in _names if n.startswith(prefix)]

    _modname = module.__name__
    modname = _modname.removeprefix('agentica_internal.cpython.shed._')
    file = module.__file__

    functions = []
    add_function = functions.append

    classes = []
    add_class = classes.append

    names = []
    addname = names.append
    newdict = {}
    additem = newdict.__setitem__

    sys_mod: ModuleType = sys_modules.get(modname, NotImplemented)

    getname = module.__dict__.get
    for _name in _names:
        name = _name
        if prefix:
            if not _name.startswith(prefix):
                continue
            name = _name.removeprefix(prefix)

        obj = getname(_name, NOT_THERE)
        if obj is NOT_THERE:
            continue

        sys_obj = getattr(sys_mod, name, NotImplemented)

        if isinstance(obj, FunctionType):
            obj.___shed_obj___ = True
            obj.___shed_ori___ = sys_obj
            obj.___shed_src___ = fun_source(obj, file)
            obj.__module__ = modname
            obj.__qualname__ = obj.__name__ = name
            add_function(obj)

        elif isinstance(obj, type):
            obj.___shed_obj___ = True
            obj.___shed_ori___ = sys_obj
            obj.___shed_src___ = cls_source(obj, file)
            obj.__module__ = modname
            obj.__qualname__ = obj.__name__ = name
            for fieldname, field in obj.__dict__.items():
                if isinstance(field, (classmethod, staticmethod)):
                    field = field.__wrapped__
                    sys_obj = getattr(sys_obj, '__wrapped__', NotImplemented)
                if isinstance(field, FunctionType):
                    field.___shed_obj___ = True
                    field.___shed_ori___ = sys_obj
                    field.___shed_src___ = fun_source(field, file)
                    field.__module__ = modname
                    field.__qualname__ = f'{name}.{fieldname}'
            add_class(obj)
        additem(name, obj)
        addname(name)

    newdict['__all__'] = names
    newdict['__CLASSES__'] = classes
    newdict['__FUNCTIONS__'] = functions
    newdict['___shed_obj___'] = True
    newdict['___shed_ori___'] = sys_mod
    newmod = ModuleType(module.__name__)
    newmod.__dict__.update(newdict)
    return newmod


def cls_source(cls: type, file: str):
    lines = []
    lineno = 1
    header = f'class {cls.__name__}'
    while not getline(file, lineno).startswith(header):
        lineno += 1
    while True:
        line = getline(file, lineno)
        if line.startswith('##'):
            break
        lines.append(line)
        lineno += 1
    return '\n'.join(lines).strip()


def fun_source(fun: FunctionType, file: str):
    lineiter = fun.__code__.co_lines()
    linenos = [n for s, e, n in lineiter if type(n) is int]
    start = min(linenos)
    end = max(linenos)
    lines = [getline(file, lineno) for lineno in range(start, end + 1)]
    return '\n'.join(lines)


class _ShedModuleCache(dict[str, ModuleType]):
    def __missing__(self, mod_name: str):
        key = mod_name
        mod_name = mod_name.replace('.', '_')
        mod_name = f'agentica_internal.cpython.shed._{mod_name}'
        if mod_name in sys_modules:
            del sys_modules[mod_name]
        try:
            prefix = '_' if key == 'builtins' else ''
            T.overload = _patched_overload  # type: ignore
            mod = import_module(mod_name)
            mod = process_module(mod, prefix)
            self[key] = mod
            return mod
        except ImportError:
            T.overload = _original_overload
            pass
        return FALLBACK_MODULE


class _ShedFunctionCache(dict[tuple[str, str], FunctionType]):
    def __missing__(self, tup: tuple[str, str]):
        mod_name, func_name = tup
        mod = _shed_module_cache[mod_name]
        if mod is not FALLBACK_MODULE:
            func = mod.__dict__.get(func_name, FALLBACK_FUNCTION)
            if func is not FALLBACK_FUNCTION:
                return func

        def fallback_func(*args, **kwargs): ...

        fallback_func.__module__ = mod_name
        fallback_func.__name__ = fallback_func.__qualname__ = func_name
        return fallback_func


class _ShedClassCache(dict[type, type]):
    def __missing__(self, cls: type):
        mod = _shed_module_cache[cls.__module__]
        if mod is FALLBACK_MODULE:
            return FALLBACK_CLASS
        attr = mod.__dict__.get(cls.__name__, FALLBACK_CLASS)
        if attr is FALLBACK_CLASS:
            return FALLBACK_CLASS
        attr.__doc__ = cls.__doc__
        assert isinstance(attr, type)
        assert not (attr.__flags__ & 256)
        return attr


RawMethod = FunctionType | staticmethod | classmethod


class _ShedMethodCache(dict[tuple[type, str], RawMethod]):
    def __missing__(self, tup: tuple[type, str]):
        cls, name = tup
        shed_cls = _shed_class_cache[cls]
        if shed_cls is not FALLBACK_CLASS:
            meth = shed_cls.__dict__.get(name, FALLBACK_METHOD)
            if meth is not FALLBACK_METHOD and isinstance(meth, RAW_METHOD_TYPES):
                return meth

        def fallback_meth(*args, **kwargs): ...

        fallback_meth.__module__ = cls.__module__
        fallback_meth.__name__ = name
        fallback_meth.__qualname__ = f'{cls.__name__}.{name}'
        return fallback_meth


RAW_METHOD_TYPES = (FunctionType, staticmethod, classmethod)


_shed_module_cache = _ShedModuleCache()
_shed_function_cache = _ShedFunctionCache()
_shed_class_cache = _ShedClassCache()
_shed_method_cache = _ShedMethodCache()


def get_shed_module(mod_name: str):
    return _shed_module_cache[mod_name]


def get_shed_function(mod_name: str, func_name: str) -> FunctionType:
    key = mod_name, func_name
    return _shed_function_cache[key]


def get_shed_class(cls: type) -> type:
    return _shed_class_cache[cls]


# this is the *raw* function, straight from the dict
def get_shed_method(cls: type, meth_name: str) -> RawMethod:
    key = cls, meth_name
    return _shed_method_cache[key]


FALLBACK_MODULE = ModuleType('<notfound>')


class FALLBACK_CLASS:
    def FALLBACK_METHOD(self, *args, **kwargs):
        pass


FALLBACK_METHOD = FALLBACK_CLASS.__dict__['FALLBACK_METHOD']


def FALLBACK_FUNCTION(*args, **kwargs):
    pass
