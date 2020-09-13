from .. import EventPayloadBase

class KyoukaCoreEventBase(EventPayloadBase):...

class Register(KyoukaCoreEventBase):
    '''已经注册成功并且消息循环正常运行了'''