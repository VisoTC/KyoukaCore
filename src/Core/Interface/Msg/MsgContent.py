from io import BufferedIOBase, BufferedReader, BytesIO, UnsupportedOperation
import re
from typing import List, Union
from typing import Union
import requests
import imghdr
from ...Exception import KyoukaMSGException, MsgContentTypeUnsupported


class MsgContent():
    def __init__(self) -> None:
        self._msgType = "MsgType"

    @property
    def msgType(self): return self._msgType


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
    def __init__(self, atUser: List[int] = list()) -> None:
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
    为了防止跨bridge转发
    """

    def __init__(self, bridge: str, flag) -> None:
        self._bridge = bridge
        self._flag = flag

    def flag(self, bridge):
        """
        判断消息是不是由这个 bridge 发送的
        """
        if bridge == self._bridge:
            return self._flag
        else:
            return False


class PicMsg(MsgContent):
    """图片消息"""
    _picBuff = None

    def __init__(self, picBuff: BufferedIOBase, forword: Union[PicMsgForword, bool] = False) -> None:
        """
        注意，图片内容将会被拷贝到内存，若处理完成请及时释放
        :parmam picBuff: 流
        :parmam forword: 转发标记，若无就无
        """
        self.__WebImg = None
        self._picBuff = self.__loadImg(picBuff)
        self.isLoaded = True
        self._forword = forword if forword != False else PicMsgForword(
            False, False)

    def __loadImg(self, picBuff: BufferedIOBase):
        if not picBuff.seekable() and picBuff.tell() != 0:
            raise UnsupportedOperation
        else:
            picBuff.seek(0)
        Buff = picBuff.read()
        Buff = BytesIO(Buff)
        picBuff.seek(0)
        if imghdr.what(None, h=Buff.getvalue()) is None:  # 不是图片就报错
            raise MsgContentTypeUnsupported
        return Buff

    @property
    def pic(self) -> BytesIO:
        if not self.isLoaded:
            self.__loadWebImg()
        self._picBuff.seek(0)
        return self._picBuff

    @property
    def forword(self):
        return self._forword

    def __del__(self):
        if self._picBuff != None:
            self._picBuff.close()  # 释放流

    @classmethod
    def webImg(cls, url, params=dict(), forword: Union[PicMsgForword, bool] = False):
        """
        从 Web 载入图片，在调用 pic 属性的时候才会触发获取操作
        """
        self = cls.__new__(cls)
        self.__WebImg = {
            'url': url,
            'params': params
        }
        self._picBuff = None
        self.isLoaded = False
        self._forword = forword if forword != False else PicMsgForword(
            False, False)

        return self

    def __loadWebImg(self):
        if self.isLoaded or self.__WebImg is None:
            raise KyoukaMSGException
        r = requests.get(self.__WebImg['url'], params=self.__WebImg['params'])
        if r.status_code < 300:
            self._picBuff = BytesIO(r.content)
            self.isLoaded = True
        else:
            raise KyoukaMSGException
