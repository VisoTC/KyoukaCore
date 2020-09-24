import logging
from typing import Any, Callable, List
import time
import threading

class RemoveCron(Exception):
    """移除这个任务"""

class NotExecutedx(Exception):
    """不执行"""


class Cron():
    def __init__(self, interval: float, func: Callable,context:List[Any] = list()) -> None:
        """创建一个定时对象"""
        self._interval = interval
        self._func = func
        self.__lastExecuted = 0
        self.__laststatus = None
        self.__context = context

    @property
    def lastExecutedStatus(self):
        '''上次执行状态'''
        return self.__laststatus

    @property
    def lastExecuted(self):
        '''上次执行时间'''
        return self.__lastExecuted

    @property
    def nextExecuted(self):
        '''下次执行时间'''
        return self.__lastExecuted + self._interval

    @property
    def allowExecuted(self):
        """判断能不能执行"""
        return self.nextExecuted <= time.time()

    def executed(self, force=False):
        if self.allowExecuted or force:
            self.__lastExecuted = time.time()
            try:
                result = self._func(self.__context)
                if result == False:
                    self.__laststatus = False
                else:
                    self.__laststatus = True
            except Exception as e:
                self.__laststatus = False
                raise e
        else:
            raise NotExecutedx

class CronManager():
    def __init__(self) -> None:
        self._callThread = threading.Thread(
            target=self.main, name="PCR Cron Thread")
        self._threadLock = threading.Lock()
        self.__cronQueue: List[Cron] = []
        self._nextTime: int = -1  # 下次执行时间
        self._nextExecutedCron: List[Cron] = []  # 执行的列表

    def start(self):
        self._callThread.start()

    def main(self):
        while True:
            with self._threadLock:
                if self._nextTime <= time.time():
                    remove = []
                    for corn in self._nextExecutedCron:
                        try:
                            corn.executed()
                        except RemoveCron:
                            remove.append(corn)
                        except NotExecutedx:
                            pass
                        except Exception as e:
                            logging.exception(e)
                            pass
                    for r in remove:
                        self.__cronQueue.remove(r)
                    self._checkNextCron()
            time.sleep(1)

    def _checkNextCron(self):
        self._nextTime = -1
        self._nextExecutedCron: List[Cron] = []
        for cron in self.__cronQueue:
            if self._nextTime == -1:
                self._nextTime = cron.nextExecuted
            if self._nextTime > cron.nextExecuted:
                self._nextExecutedCron = [cron]
                self._nextTime = cron.nextExecuted
            elif self._nextTime == cron.nextExecuted:
                self._nextExecutedCron.append(cron)
            else:
                continue

    def append(self, cron: Cron):
        with self._threadLock:
            self.__cronQueue.append(cron)
            self._checkNextCron()
