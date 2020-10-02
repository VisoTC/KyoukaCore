from . import BaseModel
from peewee import IntegerField, CharField, PrimaryKeyField,BigIntegerField,BooleanField


class Reserve(BaseModel):
    id = PrimaryKeyField()
    period = CharField(help_text="期数")
    stage = IntegerField(help_text="阶段")
    step = IntegerField(help_text="位置")
    group = IntegerField(help_text="群 id")
    member = BigIntegerField(help_text="成员 id")

    class Meta:
        db_table = 'reserve'