# fmt: off

import re

from os import getenv
from sys import __stderr__ as STDERR
# from .log_streams import write_err

from .log_env import get_log_tags
from .log_groups import *

__all__ = [
    'should_log_cls',
    'should_log_tag',
    'cls_log_tags',
]

###############################################################################

def tag_match(tags_set: set[str], tags_str: str):
    if tags_str == 'all' and '__' not in tags_set:
        return True
    if tags_str == '1' and '_' and '__' not in tags_set:
        return True
    tags_set = set(t.lower() for t in tags_set)
    tags_str = GROUP_RE.sub(lambda g: GROUP_EXPAND(g.group(0)), tags_str)
    if '+' not in tags_str:
        return tags_str in tags_set
    if not any(tag in tags_str for tag in tags_set):
        return False
    return bool(set(tags_str.split('+')).intersection(tags_set))

GROUP_RE = re.compile(rf'\b({'|'.join(GROUP_NAMES)})\b')

###############################################################################


###############################################################################

def should_log_tag(default: bool, tags: set[str]) -> bool:
    curr = get_log_tags()
    if curr == 'ALL':
        flag = '__' not in tags
    elif curr == '1':
        flag = '_' not in tags and '__' not in tags
    elif curr:
        flag = tag_match(tags, curr.lower())
    else:
        flag = bool(default)
    if getenv('AGENTICA_DEBUG_TAGS') == '1':
        STDERR.write(f"should_log_tag({default}, {tags}; env={curr!r}) => {flag}\n")
    return flag


def should_log_cls(flag: bool, cls: type):
    return should_log_tag(flag, cls_log_tags(cls))

###############################################################################

def cls_log_tags(cls: type) -> set[str]:
    if tags := CLS_LOG_TAGS.get(cls):
        return tags
    name = cls.__name__
    tagset = {name.lower()}
    extra = getattr(cls, 'LOG_TAGS', ())
    if isinstance(extra, str):
        extra = (extra,)
    tagset |= set(e.lower() for e in extra)
    for base in cls.__bases__:
        if not base.__flags__ & 256:
            tagset |= set(cls_log_tags(base))
    CLS_LOG_TAGS[cls] = tags = set(tagset)
    return tags

CLS_LOG_TAGS: dict[type, set[str]] = {}
