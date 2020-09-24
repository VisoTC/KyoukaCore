from . import BaseModel
from peewee import IntegerField, CharField, PrimaryKeyField,BigIntegerField,BooleanField


class Bind(BaseModel):
    id = PrimaryKeyField()
    group = IntegerField(help_text="群 id")
    member = BigIntegerField(help_text='成员 id',null=True)
    playerID = BigIntegerField(help_text='游戏内玩家 id')
    playerName = CharField(help_text='游戏内最新名称，若找不到尝试通过 player_id 匹配',null=True)

    class Meta:
        db_table = 'bind'