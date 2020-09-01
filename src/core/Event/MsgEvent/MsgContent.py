from io import BufferedIOBase, BytesIO, UnsupportedOperation
from typing import Any, Dict, List, Union
from typing import Union
import requests
import imghdr
from .exception import DownloadFailPicException, UnknowPicTypeException


class MsgContent():
    ...


class TextMsg(MsgContent):
    """文本消息"""

    def __init__(self, content: str) -> None:
        """
        文本消息
        @param content: 消息内容
        @param atUser: 被@的用户的id
        """
        self._content = content

    @property
    def content(self): return self._content

    def __str__(self) -> str:
        return self.content


class AtMsg(MsgContent):
    def __init__(self, atUser: Union[List[int], int] = list()) -> None:
        """
        At 指定用户
        @param atUser: 被@的用户的id
        """
        if not isinstance(atUser, list):
            atUser = [atUser]
        _atUser = []
        for u in atUser:
            _atUser.append(str(u))
        self.atUser = _atUser


class PicMsgForword():
    """
    转发标记
    为了防止跨bridge转发
    """

    def __init__(self, bridge: Union[object, bool], flag: Union[object, bool]) -> None:
        self._bridge = bridge
        self._flag = flag

    def flag(self, bridge: str):
        """
        判断消息是不是由这个 bridge 发送的
        """
        if bridge == self._bridge:
            return self._flag
        else:
            return False


class PicMsg(MsgContent):
    """图片消息"""
    _picBuff: Union[BytesIO, dict[str, Union[str]]]

    def __init__(self, picBuff: BufferedIOBase, forword: Union[PicMsgForword, bool] = False) -> None:
        """
        :parmam picBuff: 流
        :parmam forword: 转发标记，若无就无
        """
        self._picBuff = self.__loadImg(picBuff)
        self._forword = forword if forword != False else PicMsgForword(
            False, False)

    def __loadImg(self, picBuff: BufferedIOBase):
        if not picBuff.seekable() and picBuff.tell() != 0:
            raise UnsupportedOperation
        else:
            picBuff.seek(0)
        Buff = BytesIO(picBuff.read())
        picBuff.seek(0)
        if imghdr.what(None, h=Buff.getvalue()) is None:  # 不是图片就报错
            raise UnknowPicTypeException
        return Buff

    @property
    def pic(self):
        if not isinstance(self._picBuff, BytesIO):
            self._picBuff = self.__loadWebImg()
        self._picBuff.seek(0)
        return self._picBuff.getvalue()

    @property
    def forword(self):
        return self._forword

    def __del__(self):
        if isinstance(self._picBuff, BytesIO):
            self._picBuff.close()  # 释放流

    @classmethod
    def webImg(cls, url: str, params: Dict[str, str] = dict(), forword: Union[PicMsgForword, bool] = False):
        """
        从 Web 载入图片，在调用 pic 属性的时候才会触发获取操作
        """
        self = cls.__new__(cls)
        self._picBuff = {
            'url': url,
            'params': params
        }
        self._forword = forword if forword != False else PicMsgForword(
            False, False)

        return self

    def __loadWebImg(self):
        if not isinstance(self._picBuff, dict):
            raise DownloadFailPicException
        r = requests.get(self._picBuff['url'], params=self._picBuff['params'])
        if r.status_code < 300:
            self._picBuff = BytesIO(r.content)
        else:
            raise DownloadFailPicException
        return self._picBuff
