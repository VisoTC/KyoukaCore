from typing import Dict, List


class PCRBaseException(Exception):
    """PCR 插件基础错误类"""


class BigFunAPIisLogin(PCRBaseException):
    '''BigFunAPI 已经登录'''


class StepNotFound(PCRBaseException):
    """阶段字段不存在"""


class NotFoundPlayerMapping(PCRBaseException):
    """找不到对应用户的映射表"""


class DuplicateNameError(PCRBaseException):
    """有用户重名"""

    def __init__(self, l: Dict[str, List[int]]) -> None:
        self.list = l
