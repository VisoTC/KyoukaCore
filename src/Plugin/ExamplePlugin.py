from Core.Service.Plugin import PluginService, ServiceInfo
from Core.Event.MsgEvent.MsgInfo import PrivateMsgInfo
from Core.Event.MsgEvent.MsgContent import TextMsg
from Core.Event.MsgEvent import MsgEvent
from Core.Event import ReceiveEvent

example = PluginService(ServiceInfo(**{
    'packageName': "com.visotc.KyoukaCore.ExamplePlugin",
    'name': "测试插件",
    'version': "dev",
    'author': "VisoTC"
}))


@example.register("register")
def register(data):
    # 唯一可以阻塞的方法，此方法将会启动单独线程去运行，若有需要可以直接用于实现自己的逻辑
    example.logger.info("is register!")


@example.register(PrivateMsgInfo)
def onPrivateMsgInfo(event: ReceiveEvent):
    payload = event.payload
    if isinstance(payload ,MsgEvent):
        f = payload.msgContent[0]
        if isinstance(f, TextMsg):
            if f.content == "test":
                example.api.reply(event,TextMsg("i'm Here"))

example.initDone()
