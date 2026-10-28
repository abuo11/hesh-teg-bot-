import logging
import re
import sys


class SecretFilter(logging.Filter):
    """Tokenlarni logdan yashiradi."""

    PATTERNS = [
        re.compile(r"\d{6,}:[A-Za-z0-9_-]{20,}"),
        re.compile(r"(access_token=)[^&\s]+"),
        re.compile(r"(key=)[^&\s]+"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for p in self.PATTERNS:
            msg = p.sub(lambda m: (m.group(1) if m.groups() else "") + "***", msg)
        record.msg, record.args = msg, ()
        return True


def setup_logger() -> logging.Logger:
    log = logging.getLogger("hashtag_ai")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    h.addFilter(SecretFilter())
    log.addHandler(h)
    return log


logger = setup_logger()
