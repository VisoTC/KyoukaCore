from . import BaseModel
from peewee import IntegerField, CharField, PrimaryKeyField,BigIntegerField,BooleanField


class APIAuthInfo(BaseModel):
    id = PrimaryKeyField()
    botUid = BigIntegerField(help_text="关联的 Bot Uid")
    gid = BigIntegerField(help_text="群 id")
    cookie = CharField(help_text="API Cookie")

    class Meta:
        db_table = 'APIAuthInfo'