# EXCLUDE_FROM_SDK_BUILD
# fmt: off
# ruff: noqa

# NOTE: this is to ensure that componentize will acquire these modules

import site
import importlib

import agentica_internal.core.asserts
import agentica_internal.core.color
import agentica_internal.core.debug
import agentica_internal.core.eval
import agentica_internal.core.fmt
import agentica_internal.core.filters
import agentica_internal.core.fns
import agentica_internal.core.futures
import agentica_internal.core.hashing
import agentica_internal.core.json
import agentica_internal.core.log
import agentica_internal.core.make
import agentica_internal.core.print
import agentica_internal.core.queues
import agentica_internal.core.recursion
import agentica_internal.core.result
import agentica_internal.core.sentinels
import agentica_internal.core.strs
import agentica_internal.core.type
import agentica_internal.core.utils

import agentica_internal.cpython.alias
import agentica_internal.cpython.classes.anno
import agentica_internal.cpython.classes.sys
import agentica_internal.cpython.code
import agentica_internal.cpython.class_info
import agentica_internal.cpython.exceptions
import agentica_internal.cpython.frame
import agentica_internal.cpython.function
import agentica_internal.cpython.ids
import agentica_internal.cpython.inspection
import agentica_internal.cpython.iters
import agentica_internal.cpython.module
import agentica_internal.cpython.overloads
import agentica_internal.cpython.properties
import agentica_internal.cpython.slots

import agentica_internal.warpc.data.all
import agentica_internal.warpc.data.signature_compile
import agentica_internal.warpc.data.signature_utils

import agentica_internal.warpc.request.all
import agentica_internal.warpc.resource.all
import agentica_internal.warpc.resource.virtual_builtin
import agentica_internal.warpc.resource.vbuiltins

import msgspec
import rich

__all__ = []
