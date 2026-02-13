from pathlib import Path

from ..core.datetime import time_now_utc


class AgenticaError(Exception):
    """Base class for all server or client Agentica errors."""

    uid: str | None = None
    iid: str | None = None
    session_id: str | None = None
    session_manager_id: str | None = None
    error_timestamp: str | None = None
    error_log_file: str | None = None

    def __str__(self) -> str:
        msg = super().__str__()

        context_parts = []
        add = context_parts.append

        if uid := self.uid:
            add(f"UID: {uid}")
        if iid := self.iid:
            add(f"IID: {iid}")
        if session_manager_id := self.session_manager_id:
            add(f"Session Manager ID: {session_manager_id}")
        if session_id := self.session_id:
            add(f"Session: {session_id}")
        if time := self.error_timestamp:
            add(f"Time: {time}")

        if context_parts:
            msg += f"\n\nContext: {', '.join(context_parts)}"

        if error_log_file := self.error_log_file:
            msg += f"\n\nLocal log file: '{error_log_file}'"

        if context_parts or error_log_file:
            msg += "\n\nIf you require customer support, please contact hello@symbolica.ai with the error details above."
            msg += "\n\nIf you would like to file a bug report or feature request, please do so in the corresponding component's GitHub repository."
            msg += "\n\nIf unsure, please report at https://github.com/symbolica-ai/agentica-python-sdk/issues."

        return msg


def enrich_error(
    error: Exception,
    *,
    uid: str | None = None,
    iid: str | None = None,
    session_id: str | None = None,
    session_manager_id: str | None = None,
    error_log_path: Path | None = None,
) -> Exception:
    if isinstance(error, AgenticaError):
        if uid is not None:
            error.uid = uid
        if iid is not None:
            error.iid = iid
        if session_id is not None:
            error.session_id = session_id
        if session_manager_id is not None:
            error.session_manager_id = session_manager_id
        if error_log_path is not None:
            from agentica_internal.core.log import write_ring_buffer

            if error_log_file := write_ring_buffer(error_log_path):
                error.error_log_file = error_log_file
        error.error_timestamp = time_now_utc()
    return error
