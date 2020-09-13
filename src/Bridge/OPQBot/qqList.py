from . import service
from .webAPI import api
from Core.Service.UserObj import *
import json
import requests


def getFriendAndGroupList():
    """
    载入用户列表与群组列表
    """
    service.api.updateFriendsList(getUserList())
    service.api.updateGroupsList(getGroupList())


def getUserList():
    i = -1
    FriendList = Users()
    while i != 0:
        if i == -1:
            i = 0
        _payload = json.dumps({"StartIndex": i}, ensure_ascii=False)
        resp = requests.post(api, params={
            'qq': service.config['qq'],
            'funcname': 'GetQQUserList',
            'timeout': 10
        }, data=_payload.encode("UTF-8"))
        result = resp.json()
        for u in result['Friendlist']:
            FriendList.append(
                User(u['FriendUin'], u['NickName'])
            )
        i = result['StartIndex']
    return FriendList


def getGroupList():
    NextToken = None
    GroupList = Groups()
    while NextToken != "":
        if NextToken == None:
            NextToken = ""
        _payload = json.dumps({"NextToken": NextToken}, ensure_ascii=False)
        resp = requests.post(api, params={
            'qq': service.config['qq'],
            'funcname': 'GetGroupList',
            'timeout': 20
        }, data=_payload.encode("UTF-8"))
        result = resp.json()
        for g in result['TroopList']:
            GroupList.append(
                Group(g['GroupId'], g['GroupName'], g['GroupOwner'],
                      getGroupMemberList(g['GroupId']))
            )
        NextToken = result['NextToken']
    return GroupList


def getGroupMemberList(gid: int):
    LastUin = -1
    MemberList = GroupMembers()
    while LastUin != 0:
        if LastUin == -1:
            LastUin == 0
        _payload = json.dumps(
            {"GroupUin": int(gid), "LastUin": LastUin}, ensure_ascii=False)
        resp = requests.post(api, params={
            'qq': service.config['qq'],
            'funcname': 'GetGroupUserList',
            'timeout': 10
        }, data=_payload.encode("UTF-8"))
        result = resp.json()
        for gm in result['MemberList']:
            MemberList.append(
                GroupMember(gm['MemberUin'],
                            gm['GroupCard'] if gm['GroupCard'] != "" else gm['NickName'],
                            gm['GroupAdmin'] == 1)
            )
        LastUin = result['LastUin']
    return MemberList
