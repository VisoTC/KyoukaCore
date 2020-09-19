from Core.Service.Plugin import PluginService, ServiceInfo
from Core.Event.MsgEvent.MsgInfo import GroupMsgInfo, PrivateMsgInfo
from Core.Event.MsgEvent.MsgContent import TextMsg
from Core.Event.MsgEvent import MsgEvent
from Core.Event import ReceiveEvent
from Core.Service.Command import Command

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
def onPrivateMsgInfo(event: ReceiveEvent[MsgEvent]):
    payload = event.payload
    f = payload.msgContent[0]
    if isinstance(f, TextMsg):
        if f.content == "test":
            example.api.reply(event, TextMsg("i'm Here"))


def cTest(event: ReceiveEvent[MsgEvent], echotext):
    example.api.reply(event, TextMsg("echo: " + echotext))


a = Command("echo", doc="复读机", msgtypes=None, func=cTest)
command = Command("test", '示例命令', msgtypes=PrivateMsgInfo, sub=[
                  a, 
                  Command("G", "这个命令只能从群聊中看到", msgtypes=GroupMsgInfo, sub=a), 
                  Command("P", "这个命令只能从私聊中看到", msgtypes=PrivateMsgInfo, sub=a)])
example.registerCommand(command)
example.initDone()
