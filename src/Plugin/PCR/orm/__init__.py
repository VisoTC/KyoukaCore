from peewee import Model,MySQLDatabase
from playhouse.shortcuts import ReconnectMixin

class ReconnectMySQLDatabase(ReconnectMixin,MySQLDatabase):...

db = ReconnectMySQLDatabase(None)


class BaseModel(Model):

    class Meta:
        database = db
