from typing import Any


class ReadOnly():
    """
    只读类，执行 self.readOnlyLock() 后将会屏蔽写入操作
    """
    __readOnlyLock = False

    def _readOnlyLock(self):
        self.__readOnlyLock = True

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__readOnlyLock:
            raise AttributeError('{}.{} is READ ONLY'.
                                 format(type(self).__name__, name))
        else:
            return super().__setattr__(name, value)
