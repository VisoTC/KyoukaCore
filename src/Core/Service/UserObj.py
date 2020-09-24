import collections
from typing import List, Optional, Iterable, Union

from .exception import NotFoundGroup, NotFoundUser


class User(collections.UserDict):
    def __init__(self, uid: int, nickName: str) -> None:
        super().__init__()
        self.data['uid'] = uid
        self.data['nickName'] = nickName

    @property
    def uid(self): return self.data['uid']

    @property
    def nickName(self): return self.data['nickName']


class Users(collections.UserList):
    def __init__(self, initlist: Optional[Iterable[User]] = None) -> None:
        return super().__init__(initlist)

    def append(self, value: User) -> None:
        if not isinstance(value, User):
            raise TypeError
        super().append(value)

    def get(self, uid) -> User:
        """
        获得指定 uid 的信息
        """
        for user in self.data:
            if user.uid == uid:
                return user
        else:
            raise NotFoundUser


class GroupMember(User):
    def __init__(self, uid: int, nickName: str, isAdmin) -> None:
        super().__init__(uid, nickName)
        self.data['isAdmin'] = isAdmin
        self.isOwn = False

    @property
    def isAdmin(self):
        """
        判断这个成员是不是管理员、群主
        """
        if self.isOwn:
            return True
        return self.data['isAdmin']


class GroupMembers(collections.UserList):
    def __init__(self, initlist: Optional[Iterable[GroupMember]] = None) -> None:
        return super().__init__(initlist)

    def append(self, value: GroupMember) -> None:
        if not isinstance(value, GroupMember):
            raise TypeError
        super().append(value)

    def get(self, uid) -> GroupMember:
        """
        获得指定 uid 的信息
        """
        for u in self.data:
            if u.uid == uid:
                return u
        else:
            raise NotFoundUser


class Group(collections.UserDict):
    def __init__(self, gid: int, name: str, own: Union[GroupMember, int], members: GroupMembers) -> None:
        super().__init__()
        self.data['gid'] = gid
        self.data['name'] = name
        self.data['member'] = members
        if not isinstance(own, User):
            self.data['own'] = members.get(own)
            self.data['own'].data['isAdmin'] = True  # 设定标记为管理员
        else:
            self.data['own'] = own

    @property
    def gid(self) -> int: return self.data['gid']
    @property
    def name(self) -> str: return self.data['name']
    @property
    def own(self) -> User: return self.data['own']
    @property
    def member(self) -> GroupMembers: return self.data['member']


class Groups(collections.UserList):
    def __init__(self, initlist: Optional[Iterable[Group]] = None) -> None:
        return super().__init__(initlist)

    def append(self, value: Group) -> None:
        if not isinstance(value, Group):
            raise TypeError
        super().append(value)

    def get(self, gid: int) -> Group:
        for g in self.data:
            if g.gid == int(gid):
                return g
        else:
            raise NotFoundGroup
