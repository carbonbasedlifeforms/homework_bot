class SendMessageError(Exception):
    """Error on send message to Telegram API."""


class YPConnectApiError(Exception):
    """Error on connect to yandex practicum API."""


class EnvVarsNotFoundException(Exception):
    """Environment variable is not found."""


class UnknownHomeWorkStatus(Exception):
    """Unknown homework status."""


class EmptyHomeworkInResponse(Exception):
    """Empty homework in response."""


class NoHomeworkNameInResponse(Exception):
    """Homework name is empty in response."""
