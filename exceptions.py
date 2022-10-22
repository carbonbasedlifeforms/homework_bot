class SendMessageError(Exception):
    """Error on send message to Telegram API."""


class EnvVarsNotFoundException(Exception):
    """Environment variable is not found."""


class UnknownHomeWorkStatus(Exception):
    """Unknown homework status."""


class NoHomeworkNameInResponse(Exception):
    """Homework name is empty in response."""
