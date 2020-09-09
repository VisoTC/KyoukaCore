from typing import Callable, List
from ..exception import KyoukaException


class CommandException(KyoukaException):
    """命令异常基础类"""

class ReceiveEventTypeErrorCommandException(CommandException):
    """ReceiveEvent类型错误"""

class SimultaneouslyDefineCommandException(CommandException):
    """不允许同时定义方法和子命令"""


class FuncNotCallableCommandException(CommandException, ValueError):
    """方法不可调用"""

class LeastOneArgsCommandException(CommandException, ValueError):
    """至少要有一个参数接收消息信息"""


class ArgsDifferentLengthCommandException(CommandException, TypeError):
    """参数长度跟匹配的长度不符合"""


class SameCommandException(CommandException, IndexError):
    """相同的命令"""


class UnSupportArgsTypeException(CommandException, AttributeError):
    """不支持命名参数"""


class MatchFailedCommandException(CommandException):
    """没有匹配到命令"""


class MatchAndCallException(CommandException):
    """匹配失败"""

    def __init__(self, t, source) -> None:
        self.type = t
        self.trace = [source]

    def addTrace(self, com: object):
        self.trace.append(com)
        return self
