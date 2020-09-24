from typing import Dict
import json

from peewee import DoesNotExist
from ..orm.apiAuthInfo import APIAuthInfo as ormAPIAuthInfo


def getAuthInfo(botUid:int,gid: int) ->Dict:
    try:
        row, _ = ormAPIAuthInfo.get_or_create(gid=gid,
                                              cookie="{}",botUid=botUid)
        return json.loads(row.cookie)
    except DoesNotExist:
        return {}


def setAuthInfo(gid: int, cookie: Dict[str, str]):
    try:
        row = ormAPIAuthInfo.get(ormAPIAuthInfo.gid == gid)
        row.cookie = json.dumps(cookie)
    except DoesNotExist:
        row = ormAPIAuthInfo.create(
            gid=gid,
            cookie=json.dumps(cookie)
        )
    row.save()
