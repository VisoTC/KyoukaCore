# 数据库操作简易封装
from abc import ABCMeta, abstractmethod
import sqlite3
from typing import Union


class DataBase(object, metaclass=ABCMeta):
    def __init__(self, url) -> None:
        """
        初始化数据库链接
        url:string - 数据库链接
        """
        pass

    def cursor(self) -> object: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def close(self) -> None: ...


class SqliteDataBase(DataBase):

    def __init__(self, url:Union[str,sqlite3.Connection]):
        if isinstance(url,sqlite3.Connection):
            self.__dataBase = url
        else:
            self.__dataBase = sqlite3.connect(url)
            
    @property
    def origin(self):
        return self.__dataBase

    def cursor(self) -> sqlite3.Cursor:
        return self.__dataBase.cursor()

    def commit(self) -> None:
        return self.__dataBase.commit()

    def rollback(self) -> None:
        return self.__dataBase.rollback()

    def close(self) -> None:
        return self.__dataBase.close()
