from re import L


class BigFunAPIBaseException(Exception):
    """基础错误类"""


class APIError(BigFunAPIBaseException):
    """API错误"""

    def __init__(self, msg) -> None:
        self.msg = msg


class NotLogin(APIError):
    """未登录"""


class BossIDError(BigFunAPIBaseException):
    """BossID不存在"""
