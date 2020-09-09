import collections
import inspect
from pydoc import Helper
from tkinter.constants import N
from turtle import goto
from typing import List, Literal, Type, Union, overload, Callable

from ..Event import ReceiveEvent


from ..utlis import ReadOnly
from .exception import SimultaneouslyDefineCommandException, FuncNotCallableCommandException, ArgsDifferentLengthCommandException
from .exception import SameCommandException, UnSupportArgsTypeException, MatchFailedCommandException
from .exception import MatchAndCallException, LeastOneArgsCommandException, ReceiveEventTypeErrorCommandException


class FuncAttr(ReadOnly):
    """
    表示一个命令的属性
    """

    def __init__(self, func: Callable) -> None:
        """
        包装一个命令，根据参数自动匹配出参数
        注意：被调用的第一个参数必须存在，用于接收事件，调用的时候不会调用命名参数
        :param func: 调用的命令
        """
        if not callable(func):
            raise FuncNotCallableCommandException
        self._func = func
        params = inspect.signature(func).parameters
        self._required = []
        self._optional = []
        self._optionalUnlimited: bool = False
        parm = iter(params.values())
        try:
            next(parm)
        except StopIteration:
            pass
        for param in parm:
            if param.kind == param.KEYWORD_ONLY:  # 必须传入命名参数就不支持
                raise UnSupportArgsTypeException
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                if param.default == param.empty:
                    self._required.append(param.name)
                else:
                    self._optional.append(param.name)
            elif param.kind == param.VAR_POSITIONAL:
                self._optionalUnlimited = True
            elif param.kind == param.POSITIONAL_ONLY:
                self._required.append(param.name)
            elif param.kind == param.VAR_KEYWORD:  # 忽略 **kwargs
                pass
            else:
                raise UnSupportArgsTypeException
        if len(params.values()) == 0 and not self._optionalUnlimited:
            raise LeastOneArgsCommandException
        self._readOnlyLock()

    def call(self, receiveEvent: ReceiveEvent, args: List[str]):
        if not self._optionalUnlimited:
            if len(self._required) <= len(args) <= len(self._required) + len(self._optional):  # 大于等于必选参数小于等于所有参数
                self._func(receiveEvent, *args)
                return True
            else:
                raise ArgsDifferentLengthCommandException
        else:
            if len(self._required) <= len(args):  # 最大支持的参数是无穷的
                self._func(receiveEvent, *args)
                return True
            else:
                raise ArgsDifferentLengthCommandException

    @property
    def argsText(self):
        r = " ".join(self._required)
        o = " ".join(self._optional)
        if self._optionalUnlimited:
            if len(o) == 0:
                o += "..."
            else:
                o += " ..."
        if len(o) == 0 and not self._optionalUnlimited:
            return r
        else:
            return " ".join([r, o])


class Command():
    """
    命令类
    """

    def __init__(self, command: str, doc: str, sub: Union[List, object, None] = None, func: Union[Callable, None] = None) -> None:
        """
        创建一条命令
        :param command: 匹配的命令
        :param doc: 帮助文档
        :param sub: 二选一，子命令，传入Command 类
        :param func: 二选一，执行的方法，可选必选参数用方法规定
        """
        self._command = command
        self._doc = doc
        if not (sub is None) ^ (func is None):
            raise SimultaneouslyDefineCommandException
        if not func is None:
            self._func = FuncAttr(func)
            self._sub: Union[None, List[Command]] = None
        else:
            if isinstance(sub, Command):
                sub = [sub]
            if isinstance(sub, list):
                _check = []
                for com in sub:
                    if com.command in _check:
                        raise SameCommandException
                    else:
                        _check.append(com.command)
                self._sub: Union[None, List[Command]] = sub
            else:
                self._sub: Union[None, List[Command]] = None
            self._func = None

    @property
    def command(self):
        return self._command

    @property
    def doc(self):
        return self._doc

    @property
    def func(self):
        """
        返回方法，如果没有就返回 None
        """
        return self._func

    @property
    def subs(self):
        """
        返回子命令列表，如果没有就返回 None
        """
        return self._sub

    def addSubCommand(self, command):
        """
        添加子命令
        :param command: 传入本类的实例
        """
        if isinstance(command, Command):
            self._sub.append(command)
        else:
            raise ValueError

    @staticmethod
    def _commandAnalysis(commandStr: str):
        if not isinstance(commandStr, str):
            raise ValueError
        holpFlag = ['"', "'"]  # 单引号双引号包裹的内容
        hold: Union[str, bool] = False  # 表示遇到指定符号忽略空格
        commands: List[str] = []
        command = ''

        for s in commandStr:
            if s in holpFlag:  # 匹配到包裹
                if hold == False:  # 如果当前保持符不是 False
                    hold = s  # 设定当前保持符号并跳过
                    continue
                else:  # 如果当前有保持符号
                    if hold == s:  # 之前的保持符号就是当前的
                        hold = False  # 取消保持符号并跳过这个符号
                        continue
            if hold == False and s == " ":  # 匹配到空格并且当前不需要忽略空格
                commands.append(command)
                command = ''
            else:
                command += s
        else:
            if command != '':
                commands.append(command)
                command = ''

        return commands

    def match(self, commands: Union[List[str], str]):
        if isinstance(commands, str):
            commands = self._commandAnalysis(commands)
        if len(commands) > 0:
            if self.command == commands[0]:
                return True
        return False

    def matchAndCall(self, commands: Union[List[str], str], receiveEvent: ReceiveEvent) -> Literal[True]:
        """
        自动匹配命令并执行
        :param commands: 分隔后的命令
        :return: 匹配并且执行后
        """
        if isinstance(commands, str):
            commands = self._commandAnalysis(commands)
        if not isinstance(receiveEvent, ReceiveEvent):
            raise ReceiveEventTypeErrorCommandException
        if self.match(commands):
            if not self.subs is None:  # 有子命令
                for sub in self.subs:
                    try:
                        return sub.matchAndCall(commands[1:], receiveEvent)
                    except MatchAndCallException as e:  # 包装的错误添加当前路径
                        e.addTrace(self)
                        raise e
                    except MatchFailedCommandException as e:
                        pass
                else:
                    raise MatchAndCallException(
                        MatchFailedCommandException, self)  # 没有匹配到命令
            elif not self.func is None:
                try:
                    return self.func.call(receiveEvent, commands[1:])
                except ArgsDifferentLengthCommandException as e:  # 参数不匹配
                    raise MatchAndCallException(  # 更改包装并且发送到外层
                        ArgsDifferentLengthCommandException, self)  # 包装的错误添加当前路径
            else:
                raise SimultaneouslyDefineCommandException
        raise MatchFailedCommandException  # 没有匹配到命令

    def __repr__(self) -> str:
        return str({"command": self.command, "doc": self.doc})
