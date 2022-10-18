class HTTPStatusOKException(Exception):
    """Server is unavailable."""

    pass


class WrongTypeOfHomeworksKey(Exception):
    """Wrong type of homeworks key."""


class UnknownHomeWorkStatus(Exception):
    """Unknown homework status."""

    pass


class HomeworksKeyIsNotExists(Exception):
    """Homeworks key is not exists."""

    pass


class EmptyHomeworkInResponse(Exception):
    """Empty homework in response."""

    pass


class NoHomeworkNameInResponse(Exception):
    """Homework name is empty in response."""

    pass
