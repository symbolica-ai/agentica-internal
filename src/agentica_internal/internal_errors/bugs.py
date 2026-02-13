"""Presumed unreachable code paths should raise errors which the user can use to report bugs."""

from typing import Any

from . import base

GITHUB_ISSUES_URL = 'https://github.com/symbolica-ai/agentica-python-sdk/issues'


class ThisIsABug(base.AgenticaError):
    """Raise this error when reaching this path in the code should be considered a bug."""

    def __init__(self, *args: Any, report_url: str | None = None, dump_path: str | None = None):
        super().__init__(f'This should not have happened: {', '.join(map(str, args))}')
        if report_url is None:
            report_url = GITHUB_ISSUES_URL
        super().add_note(f'Please file a bug report at {report_url}')
        if dump_path is not None:
            # FUTURE: auto-generate these here.
            super().add_note('Please include your crash dump: {dump_path}')
