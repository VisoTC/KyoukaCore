from threading import Event
class Result():
    def __init__(self) -> None:
        self.__isDone = Event()
        self.__result = None
    
    def result(self,timeout=15):
        """
        返回结果，若还没完成就阻塞到完成
        :param timeout: 超时时间（秒）
        :raise TimeoutError: 超时未返回数据
        """
        if self.__isDone.wait(timeout):
            return self.__result
        else:
            raise TimeoutError
    
    def set(self,result):
        """
        设置结果
        :param result: 请求的结果
        """
        self.__result = result
        self.__isDone.set()
            