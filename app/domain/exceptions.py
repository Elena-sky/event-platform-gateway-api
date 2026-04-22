"""Domain-level publish exceptions.

Hierarchy
---------
PublishError
├── PublishNotConfirmedError  — broker did not confirm in time
└── MessageReturnedError      — broker returned message (unroutable)
"""


class PublishError(Exception):
    """Base class for all publish-side failures."""


class PublishNotConfirmedError(PublishError):
    """Raised when the broker did not confirm the message within the timeout."""


class MessageReturnedError(PublishError):
    """Raised when the broker returned the message because it was unroutable."""
