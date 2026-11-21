from __future__ import annotations


class EmailError(Exception):
    pass


class EmailConfigError(EmailError):
    pass


class EmailNotFoundError(EmailError):
    pass
