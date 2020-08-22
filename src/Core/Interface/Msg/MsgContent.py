from typing import List, Union


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


class PicMsg(MsgContent):
    """图片消息"""

    def __init__(self, pic: Union[str, bytes], forword: Union[str, None] = None) -> None:
        """
        :parmam url: 图片地址
        :parmam forword: 转发标记
        """
        self._pic = pic
        self._forword = forword

    @property
    def pic(self): return self._pic

    @property
    def forword(self):
        return self._forword
