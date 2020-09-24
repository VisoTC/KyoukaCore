# 消息
from typing import Union


class MsgInfo():
    ...


class GroupMsgInfo(MsgInfo):
    def __init__(self, GroupId:int, UserId:Union[int,None]=None, GroupName:Union[str,None]=None, UserName:Union[str,None]=None) -> None:
        """
        群消息信息
        :param FromGroupId: 群号
        :param FromUserId: 发送者号码（可选）
        :param FromGroupName: 群名（可选）
        :param FromNickName: 发送者昵称（发送可选）
        """
        self._info = {
            "GroupId": int(GroupId),
            "GroupName": GroupName,
            "UserId": UserId,
            "UserName": UserName,
        }

    @property
    def GroupId(self): return self._info['GroupId']

    @property
    def GroupName(self): return self._info['GroupName']

    @property
    def UserId(self): return self._info['UserId']

    @property
    def UserName(self): return self._info['UserName']

    def __str__(self) -> str:
        return "[群:{gn}({gid})] {un}({uid})".format(**{"gn": self.GroupName, "gid": self.GroupId, "un": self.UserName, "uid": self.UserId})

class GroupPrivateMsgInfo(MsgInfo):
    def __init__(self, GroupId:int, UserId:Union[int,None]=None, GroupName:Union[int,None]=None, UserName:Union[int,None]=None) -> None:
        """
        群私聊消息信息
        :param FromGroupId: 群号
        :param FromUserId: 发送者号码（发送可选）
        :param FromGroupName: 群名（发送可选）
        :param FromNickName: 发送者昵称（发送可选）
        """
        self._info = {
            "GroupId": GroupId,
            "GroupName": GroupName,
            "UserId": UserId,
            "UserName": UserName,
        }

    @property
    def GroupId(self): return self._info['GroupId']

    @property
    def GroupName(self): return self._info['GroupName']

    @property
    def UserId(self): return self._info['UserId']

    @property
    def UserName(self): return self._info['UserName']

    def __str__(self) -> str:
        return "[群:{gn}({gid})] {un}({uid})".format(**{"gn": self.GroupName, "gid": self.GroupId, "un": self.UserName, "uid": self.UserId})

class PrivateMsgInfo(MsgInfo):
    def __init__(self, UserId:int, UserName:Union[str,None]=None) -> None:
        """
        私人消息信息
        :param FromUserId: 发送者号码
        :param FromNickName: 发送者昵称（发送可选）
        """
        self._info = {
            "UserId": UserId,
            "UserName": UserName,
        }

    @property
    def UserId(self): return self._info['UserId']

    @property
    def UserName(self): return self._info['UserName']

    def __str__(self) -> str:
        return "[私聊] {un}({uid})".format(**{"un": self.UserName, "uid": self.UserId})
