# KyoukaCore
> 一个通用的机器人平台，目的是创建平台无关的机器人平台
> 
> 正在开发中，目前兼容 Bot 框架为 [OPQBOT](https://github.com/OPQBOT/OPQ)
>
> 当前唯一指定插件为：PCR 报刀插件（开发中）

[![Build Status](https://szlytlyt.visualstudio.com/KyoukaCore/_apis/build/status/VisoTC.KyoukaCore?branchName=master)](https://szlytlyt.visualstudio.com/KyoukaCore/_build/latest?definitionId=1&branchName=master)

当前处于开发状态，随时会有更变
# 预期支持功能
- [ ] 定时器、任务计划
- [x] 命令系统
- [ ] 事件（好友申请、群聊退群加群）支持与处理
- [x] 基础消息收发（好友、群聊、临时消息）
# 开发方法
## 开发 Bridge（与机器人通讯）
```python
# 导入包
from Core.Service.Bridge import BridgeService, ServiceInfo
# 消息类别
from Core.Event.MsgEvent.MsgInfo import PrivateMsgInfo, GroupPrivateMsgInfo, GroupMsgInfo
# 接收的消息对象 
from Core.Event import ReceiveEvent
# 创建机器人对象
service = BridgeService(ServiceInfo(**{
    'packageName': "com.visotc.KyoukaCore.ExampleBridge",
    'name': "机器人桥",
    'version': "dev",
    'author': "VisoTC"
}))
service.register(PrivateMsgInfo,OnSendMsg)

@service.register(PrivateMsgInfo)
def OnSendMsg(event: ReceiveEvent)：
    # 发送消息
# 示例请查看 OPQBot
```
## 开发 Plugin（实现各种功能的）
```python
# 导入包
from Core.Service.Plugin import PluginService, ServiceInfo
# 消息类别
from Core.Event.MsgEvent.MsgInfo import PrivateMsgInfo, GroupPrivateMsgInfo, GroupMsgInfo
# 接收的消息对象 
from Core.Event import ReceiveEvent
# 创建机器人对象
service = PluginService(ServiceInfo(**{
    'packageName': "com.visotc.KyoukaCore.ExamplePlugin",
    'name': "插件",
    'version': "dev",
    'author': "VisoTC"
}))
service.register(PrivateMsgInfo,OnSendMsg)

@service.register(PrivateMsgInfo)
def OnPrivateMsgInfo(event: ReceiveEvent)：
    # 收到消息处理

# 示例请查看 ExamplePlugin
```