"""Normal logs contain event names and numeric diagnostics, never payloads."""

import logging
import re
from interview_app_backend.utils.log_events import TEMPLATES

EVENTS = {"request_complete", "lease_release_failed", "lease_renewal_failed"}
_installed = False


class PrivateFields(logging.Filter):
    def filter(self, record):
        # Extra fields are added after the factory runs. Remove them before handlers.
        standard = logging.LogRecord("", 0, "", 0, "", (), None).__dict__
        for key in list(record.__dict__):
            if key not in standard and key not in {"status_code", "duration_ms", "message", "asctime",
                                                   "provider", "model", "task", "raw_output_length"}:
                del record.__dict__[key]
        return True


def install():
    global _installed
    if _installed:
        return
    previous = logging.getLogRecordFactory()

    def private_record(*args, **kwargs):
        record = previous(*args, **kwargs)
        if isinstance(record.msg, str) and record.name == "interview.security" and record.msg in EVENTS:
            event = record.msg
        elif isinstance(record.msg, str) and record.msg in TEMPLATES:
            event = re.sub(r"%[-+0-9.]*[sdrf]", "<redacted>", record.msg)
            if record.msg.startswith("Question generation fallback root cause:") and isinstance(record.args, tuple):
                if record.args and record.args[0] in {"timeout_exceeded", "future_exception"}:
                    event = event.replace("reason=<redacted>", "reason=" + record.args[0])
            if record.msg.startswith("evaluation_model=") and isinstance(record.args, tuple):
                if len(record.args) > 3 and record.args[3] in {"repaired", "passed", "failed"}:
                    event = event.replace("validation=<redacted>", "validation=" + record.args[3])
        else:
            event = "diagnostic_event"
        if record.exc_info and isinstance(record.exc_info, tuple):
            category = {"TimeoutError": "timeout", "DeadlineExceeded": "deadline", "ValueError": "validation",
                        "HTTPStatusError": "upstream_http", "ConnectError": "transport"}.get(
                            getattr(record.exc_info[0], "__name__", ""), "internal")
            event += " category=" + category
        record.msg, record.args = event, ()
        record.exc_info = record.exc_text = record.stack_info = None
        return record

    logging.setLogRecordFactory(private_record)
    _installed = True


class DiagnosticFormatter(logging.Formatter):
    def format(self, record):
        output = super().format(record)
        for field in ("status_code", "duration_ms"):
            value = getattr(record, field, None)
            if type(value) is int and value >= 0:
                output += f" {field}={value}"
        return output
